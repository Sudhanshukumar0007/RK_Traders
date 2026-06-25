import openpyxl

wb = openpyxl.load_workbook("Rate of All Company (4).xlsx", data_only=True)
sheet = wb.active
print("Active sheet:", sheet.title)

current_variants = []
products_data = []

for row_idx, row in enumerate(sheet.iter_rows(min_row=7, max_col=7, values_only=True)):
    name = row[0]
    size = row[1]
    prices = row[2:7]
    
    if name is not None:
        name = str(name).strip()
    if size is not None:
        size = str(size).strip()
        
    if size:
        current_variants.append({
            "size": size,
            "prices": [p for p in prices]
        })
        
    if name and current_variants:
        if name != "Brass":
            products_data.append({
                "name": name,
                "variants": list(current_variants)
            })
        current_variants = []

print("Total Products:", len(products_data))
for p in products_data:
    print(f"Product: {p['name']} ({len(p['variants'])} variants)")
    for v in p['variants']:
        print(f"  Size: {v['size']}, Prices: {v['prices']}")
