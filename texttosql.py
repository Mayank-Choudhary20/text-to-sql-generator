import re

# --------------------------
# Schema & FK definitions
# --------------------------
# Adjust these to match your real DB schema if needed.
tables = {
    "students":       ["id", "name", "age", "score", "class"],
    "employees":      ["id", "name", "age", "salary", "email", "department", "manager_id"],
    "products":       ["id", "name", "price", "category", "stock"],
    "customers":      ["id", "name", "age", "city", "phone_number", "email"],
    "orders":         ["id", "customer_id", "product_id", "order_date", "amount", "status"]
}

# Simple foreign-key map for join inference: (from_table, col) -> (to_table, to_col)
foreign_keys = {
    ("orders", "customer_id"): ("customers", "id"),
    ("orders", "product_id"): ("products", "id"),
    ("employees", "manager_id"): ("employees", "id"),
    ("products", "category"): ("categories", "name")  # example if categories table exists
}

# --------------------------
# Utilities & Normalization
# --------------------------
def normalize_text(t: str) -> str:
    t = t.lower().strip()
    # common phrasing -> operator normalization
    t = re.sub(r"\bgreater than\b", ">", t)
    t = re.sub(r"\bmore than\b", ">", t)
    t = re.sub(r"\babove\b", ">", t)
    t = re.sub(r"\bless than\b", "<", t)
    t = re.sub(r"\bbelow\b", "<", t)
    t = re.sub(r"\bat least\b", ">=", t)
    t = re.sub(r"\bminimum\b", ">=", t)
    t = re.sub(r"\bat most\b", "<=", t)
    t = re.sub(r"\bmaximum\b", "<=", t)
    t = re.sub(r"\bequals\b", "=", t)
    t = re.sub(r"\bis\b", "=", t)
    return t

def find_tables(text: str):
    found = []
    for t in tables:
        if re.search(r"\b" + re.escape(t) + r"\b", text):
            found.append(t)
    return found

def detect_fields_in_text(text: str, table: str):
    found = []
    for f in tables.get(table, []):
        if re.search(r"\b" + re.escape(f) + r"\b", text):
            found.append(f)
    return found

# --------------------------
# Condition parsing
# --------------------------
def split_conditions(cond_text: str):
    """
    Splits condition text into tokens and connectors.
    Returns: (conditions_list, connectors_list)
    Example:
      "age > 20 and city = 'delhi' or score between 50 and 80"
    -> conditions: ["age > 20", "city = 'delhi'", "score between 50 and 80"]
       connectors: ["AND", "OR"]
    """
    # preserve quoted strings first
    cond_text = cond_text.strip()
    # split by ' and ' / ' or ' / ' not ' but keep connectors
    tokens = re.split(r"\s+(and|or|not)\s+", cond_text, flags=re.IGNORECASE)
    conditions = []
    connectors = []
    for tok in tokens:
        tok_strip = tok.strip()
        if not tok_strip:
            continue
        if tok_strip.lower() in ("and", "or", "not"):
            connectors.append(tok_strip.upper())
        else:
            conditions.append(tok_strip)
    return conditions, connectors

def parse_single_condition(cond: str, default_date_col=None):
    """
    Parse a single condition fragment into SQL.
    Handles: comparisons, between, date detection, string quoting.
    Returns a SQL condition string or None if not recognized.
    """
    cond = cond.strip()

    # BETWEEN pattern: "<col> between <low> and <high>"
    m_between = re.search(r"(\w+)\s+between\s+(['\"]?[\w\-:@\.]+['\"]?)\s+and\s+(['\"]?[\w\-:@\.]+['\"]?)", cond, flags=re.IGNORECASE)
    if m_between:
        col, low, high = m_between.groups()
        low = _quote_if_string(low)
        high = _quote_if_string(high)
        return f"{col} BETWEEN {low} AND {high}"

    # comparison operator pattern: col (>=|<=|=|>|<) value
    m_comp = re.search(r"(\w+)\s*(>=|<=|=|>|<)\s*(['\"]?[\w\-:@\.]+['\"]?)$", cond)
    if m_comp:
        col, op, val = m_comp.groups()
        val = _quote_if_string(val)
        return f"{col} {op} {val}"

    # date detection: look for YYYY-MM-DD
    m_date = re.search(r"(\d{4}-\d{2}-\d{2})", cond)
    if m_date:
        date_val = m_date.group(1)
        # determine operator
        if ">" in cond or "after" in cond:
            col = default_date_col or "order_date"
            return f"{col} > '{date_val}'"
        if "<" in cond or "before" in cond:
            col = default_date_col or "order_date"
            return f"{col} < '{date_val}'"
        if "=" in cond or "on" in cond:
            col = default_date_col or "order_date"
            return f"{col} = '{date_val}'"
        # fallback
        return f"{default_date_col or 'order_date'} = '{date_val}'"

    # natural form: "<field> equals <value>" (after normalization this could be "field = value")
    m_simple = re.search(r"(\w+)\s*=\s*(['\"]?[\w\-:@\.]+['\"]?)", cond)
    if m_simple:
        col, val = m_simple.groups()
        val = _quote_if_string(val)
        return f"{col} = {val}"

    # trailing: e.g. "age 25" or "salary 50000" (implied equals)
    m_implied = re.search(r"^(\w+)\s+(['\"]?[\w\-:@\.]+['\"]?)$", cond)
    if m_implied:
        col, val = m_implied.groups()
        val = _quote_if_string(val)
        return f"{col} = {val}"

    return None

def _quote_if_string(token: str):
    """Return token quoting it if it is not purely numeric (allow negative)"""
    token = token.strip()
    # strip surrounding quotes if any
    if (token.startswith("'") and token.endswith("'")) or (token.startswith('"') and token.endswith('"')):
        return token
    # remove stray punctuation
    t = token
    # numeric (integer or float)
    if re.fullmatch(r"-?\d+(\.\d+)?", t):
        return t
    # otherwise quote
    return f"'{t}'"

# --------------------------
# JOIN inference
# --------------------------
def infer_join_clause(selected_tables):
    """
    Given a list of tables involved in the query, return:
    - from_clause (string)
    - list of tables (ordered)
    Basic strategy:
      - Start with the first table
      - Try to join to subsequent tables using known foreign_keys
      - If no mapping, perform CROSS JOIN
    """
    if not selected_tables:
        return None

    used = [selected_tables[0]]
    from_clause = selected_tables[0]
    for t in selected_tables[1:]:
        joined = False
        # try to find fk in either direction
        for (f_table, f_col), (t_table, t_col) in foreign_keys.items():
            # exact match direction
            if f_table == used[-1] and t_table == t:
                from_clause += f" JOIN {t} ON {f_table}.{f_col} = {t}.{t_col}"
                joined = True
                break
            # reverse
            if f_table == t and t_table == used[-1]:
                from_clause += f" JOIN {t} ON {t}.{f_col} = {used[-1]}.{t_col}"
                joined = True
                break
        if not joined:
            # fallback: try common column "id" vs "<table>_id"
            possible_fk = f"{t}_id"
            if possible_fk in tables[used[-1]]:
                from_clause += f" JOIN {t} ON {used[-1]}.{possible_fk} = {t}.id"
                joined = True
        if not joined:
            # fallback to CROSS JOIN
            from_clause += f", {t}"
        used.append(t)
    return from_clause

# --------------------------
# Main text -> SQL builder
# --------------------------
def text_to_sql(text: str):
    if not text or not text.strip():
        return "Empty input."

    raw = text.strip()
    norm = normalize_text(raw)

    # detect mention of multiple tables
    mentioned_tables = find_tables(norm)

    # If more than one table mentioned, we will attempt JOIN; otherwise default to single table
    if mentioned_tables:
        primary_table = mentioned_tables[0]
    else:
        # if no table found, try to infer from common keywords
        # naive fallback: if 'order' or 'orders' in text -> orders etc.
        if re.search(r"\border\b|\borders\b", norm):
            primary_table = "orders"
            mentioned_tables = ["orders"]
        elif re.search(r"\bproduct\b|\bproducts\b", norm):
            primary_table = "products"
            mentioned_tables = ["products"]
        elif re.search(r"\bcustomer\b|\bcustomers\b", norm):
            primary_table = "customers"
            mentioned_tables = ["customers"]
        elif re.search(r"\bstudent\b|\bstudents\b", norm):
            primary_table = "students"
            mentioned_tables = ["students"]
        elif re.search(r"\bemployee\b|\bemployees\b", norm):
            primary_table = "employees"
            mentioned_tables = ["employees"]
        else:
            return "Could not detect table."

    # detect fields
    select_fields = []
    # if user asked 'all' or 'show all'
    if re.search(r"\b(all|everything|show all|list all|get all)\b", norm):
        select_fields = ["*"]
    else:
        # try to extract fields for each mentioned table
        for tbl in mentioned_tables:
            found = detect_fields_in_text(norm, tbl)
            for f in found:
                # disambiguate same field across tables: use table.field if multiple tables present
                if len(mentioned_tables) > 1:
                    select_fields.append(f"{tbl}.{f}")
                else:
                    select_fields.append(f)
        # if no field detected, keep '*'
        if not select_fields:
            select_fields = ["*"]

    # infer join / from clause
    from_clause = None
    if len(mentioned_tables) > 1:
        from_clause = infer_join_clause(mentioned_tables)
    else:
        from_clause = mentioned_tables[0]

    # extract condition part: prefer after 'where' or 'with', else whole input
    cond_part_match = re.search(r"(?:where|with)\s+(.+)", norm)
    cond_text = cond_part_match.group(1) if cond_part_match else norm

    # but remove leading phrases like "show", "list", "get", "show all", table names, select fields
    cond_text = re.sub(r"^(show|get|list|find)\b", "", cond_text).strip()
    # also strip table name occurrences at start
    cond_text = re.sub(r"^(" + "|".join(re.escape(t) for t in mentioned_tables) + r")\b", "", cond_text).strip()

    # Now split into condition fragments
    conds, connectors = split_conditions(cond_text)

    sql_conditions = []
    for c in conds:
        parsed = parse_single_condition(c, default_date_col="order_date")
        if parsed:
            sql_conditions.append(parsed)
        else:
            # try to parse fragments that mention a table.field: e.g. "customers city equals delhi"
            # remove table words and try again
            c2 = c
            for t in mentioned_tables:
                c2 = re.sub(r"\b" + re.escape(t) + r"\b", "", c2).strip()
            parsed2 = parse_single_condition(c2, default_date_col="order_date")
            if parsed2:
                sql_conditions.append(parsed2)
            else:
                # ignore if cannot parse
                pass

    # Build WHERE clause joining conditions with connectors
    where_clause = ""
    if sql_conditions:
        # If connectors list shorter than needed, assume AND between remaining
        final_conditions = []
        idx_cond = 0
        idx_conn = 0
        final_conditions.append(sql_conditions[idx_cond])
        idx_cond += 1
        while idx_cond < len(sql_conditions):
            conn = "AND"
            if idx_conn < len(connectors):
                # support NOT specially
                if connectors[idx_conn] == "NOT":
                    # invert next condition by wrapping in NOT(...)
                    next_cond = sql_conditions[idx_cond]
                    final_conditions[-1] = final_conditions[-1]  # keep previous
                    final_conditions.append(f"NOT ({next_cond})")
                    idx_cond += 1
                    idx_conn += 1
                    continue
                conn = connectors[idx_conn]
            final_conditions.append(sql_conditions[idx_cond])
            final_conditions.insert(len(final_conditions)-1, conn)  # insert connector before new cond
            idx_cond += 1
            idx_conn += 1

        # The insertion above created a mixed structure; rebuild properly:
        # Simpler: join with connectors in order; if fewer connectors, use AND
        parts = []
        for i, sc in enumerate(sql_conditions):
            parts.append(sc)
            if i < len(sql_conditions) - 1:
                if i < len(connectors):
                    parts.append(connectors[i])
                else:
                    parts.append("AND")
        where_clause = " ".join(parts)

    # Final SQL
    select_part = ", ".join(select_fields)
    sql = f"SELECT {select_part} FROM {from_clause}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    sql += ";"
    return sql

# --------------------------
# Quick interactive loop & example tests
# --------------------------
if __name__ == "__main__":
    examples = [
        "Show all students",
        "Get name and age of students",
        "Show employees with salary >= 50000 and department equals sales",
        "List products where price between 100 and 500 and category equals toys",
        "Show customers with age greater than 25 and city equals delhi",
        "Show orders placed after date 2023-01-01",
        "Orders before 2022-12-31",
        "Get orders where amount > 2000 and status = pending",
        "Find employees whose manager_id = 3",
        "Show products where stock < 10 or price < 50",
        "Get customers where email = abc@example.com",
        "List orders where order_date between 2023-01-01 and 2023-03-31"
    ]

    print("=== Examples (text -> SQL) ===")
    for ex in examples:
        print("\nText:", ex)
        print("SQL: ", text_to_sql(ex))

    print("\n=== Interactive mode ===")
    while True:
        q = input("\nEnter text query (or 'exit'): ").strip()
        if q.lower() in ("exit", "quit"):
            break
        print("Generated SQL:", text_to_sql(q))
