import json
import re

raw_data = """
1. Coupler SCH 80
1/2": 9.5
1": 22
1.1/4": 32
1.1/2": 42
2": 61
3": 184
__IMAGE__: coupler_sch80.png

2. Elbow 90* SCH 80
1/2": 14
1": 32
1.1/4": 50
1.1/2": 67
2": 100.5
3": 304
__IMAGE__: elbow_sch_80.png

3. Tee SCH 80
1/2": 17
1": 44
1.1/4": 66.5
1.1/2": 89
2": 143
3": 413.5
__IMAGE__: tee_sch80.png

4. Cross SCH 80
1/2": 22.5
1": 44
1.1/4": 171
1.1/2": 231
__IMAGE__: Cross_SCH_80.png

5. Elbow 45* SCH 80
1/2": 11
1": 27.5
1.1/4": 42
1.1/2": 57
2": 87.5
3": 250
__IMAGE__: elbow_45degree_sch40.png

6. Union SCH 80
1/2": 34
1": 63
1.1/4": 97
1.1/2": 143
2": 184
3": 614
__IMAGE__: unicorn_sch80.png

7. Ball Valve SCH 80
1/2": 83.5
1": 194
1.1/4": 294
1.1/2": 349
2": 534
3": 2267
__IMAGE__: ball_valve_sch_80.png

8. Tank Connector SCH 80
1/2": 29
1": 60.5
1.1/4": 67
1.1/2": 76
2": 103.5
3": 292.5
__IMAGE__: tank_connector_sch80.png

9. MTA Plastic SCH 80
1/2": 7.5
1": 17
1.1/4": 30
1.1/2": 34
2": 50
3": 144
__IMAGE__: mta_plastic_sch80.png

10. FTA Plastic SCH 80
1/2": 9.5
1": 21.5
1.1/4": 30
1.1/2": 35.5
2": 60
3": 151.5
__IMAGE__: fta_plastic_sch80.png

11. Reducer SCH 80
1" x 1/2": 22
1.1/4" x 1": 31
1.1/2" x 1": 47
2" x 1": 60.5
2" x 1.1/2": 73.5
3" x 2": 153
__IMAGE__: reducer_sch_80.png

12. Reducer Bush SCH 80
1" x 1/2": 11.5
1.1/4" x 1": 13
1.1/2" x 1/2": 26
1.1/2" x 1": 24.5
1.1/2" x 1.1/4": 13
2" x 1": 38
2" x 1.1/2": 31
3" x 2": 163
__IMAGE__: reducer_bush_sch80.png

13. Reducer Tee SCH 80
1" x 1/2": 37
1.1/4" x 1": 68
1.1/2" x 1": 74
2" x 1": 133
3" x 2": 375
__IMAGE__: reducer_tee_sch80.png

14. Reducer Elbow SCH 80
1" x 1/2": 30
1.1/4" x 1": 80
1.1/2" x 1": 88
2" x 1": 265
__IMAGE__: reducer_elbow_sch80.png

15. End Cap SCH 80
1/2": 6.5
1": 15
1.1/4": 23
1.1/2": 32
2": 46.5
3": 129.5
__IMAGE__: endcap_sch80.png

16. Bypass Bend SCH 80
1/2": 52
1": 117
1.1/4": 143
1.1/2": 194
2": 392
__IMAGE__: bypass_bend_sch_80.png

17. Brass Elbow SCH 80
1/2": 98
3/4": 151.5
1" x 1/2": 141
1": 319
__IMAGE__: brass_elbow_sch_80.png

18. Brass Tee SCH 80
1/2": 115
3/4": 157
1" x 1/2": 153
1": 212
__IMAGE__: brass_tee_sch80.png

19. Brass MTA SCH 80
1/2": 131
1": 234
1.1/4": 422
1.1/2": 519.5
2": 722
3": 1792
1" x 1/2": 162
__IMAGE__: brass_mta_sch80.png

20. Brass FTA SCH 80
1/2": 88
1": 244
1.1/4": 323.5
1.1/2": 400
2": 691
3": 1646
1" x 1/2": 116
__IMAGE__: brass_fta_sch80.png
"""

products = []
current_prod = None

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

for line in raw_data.strip().split('\n'):
    line = line.strip()
    if not line:
        continue
    if line.startswith('__IMAGE__:'):
        current_prod['image'] = line.split('__IMAGE__:')[1].strip()
    elif re.match(r'^\d+\.', line):
        name = line.split('.', 1)[1].strip()
        cat = "Brass Fittings" if "Brass" in name else "SCH 80 Fittings"
        cat_slug = slugify(cat)
        current_prod = {
            "name": name,
            "slug": slugify(name),
            "category_slug": cat_slug,
            "brand_slug": "supreme",
            "component_type": name.split('SCH')[0].strip() if 'SCH' in name else name,
            "material": "Brass" if "Brass" in name else "UPVC",
            "pressure_rating": "SCH-80",
            "description": f"High quality {name} for plumbing applications.",
            "variants": []
        }
        products.append(current_prod)
    else:
        parts = line.split(':')
        if len(parts) == 2:
            size, price = parts
            sku = slugify(current_prod['name'] + '-' + size.strip())
            current_prod['variants'].append({
                "size_label": size.strip(),
                "sku": sku.upper(),
                "mrp": float(price.strip()),
                "stock": 100
            })

print("PRODUCTS = " + json.dumps(products, indent=4))
