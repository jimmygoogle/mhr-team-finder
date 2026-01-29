# def include_object(object, name, type_, reflected, compare_to):
#     # Skip PostGIS-owned system tables
#     if name in ("spatial_ref_sys", "geometry_columns", "geography_columns"):
#         return False
#     # Skip tiger/topology schema tables if needed
#     if object.schema in ("tiger", "topology"):
#         return False
#     return True
