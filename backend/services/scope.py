"""A scalar facility or an organization's explicit set of facilities."""
def scope_filter(column, scope):
    return column.in_(scope) if isinstance(scope, (list, tuple)) else column == scope
