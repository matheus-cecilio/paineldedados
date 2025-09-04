import io
import pandas as pd
from datetime import datetime, timedelta

cols = ["SKU", "Product", "Category", "Price", "Quantity", "Customer Name", "Customer Email", "Sale Date"]
rows = []
base_date = datetime.utcnow().date()
for i in range(30):
    rows.append({
        "SKU": f"SKU-{1000+i}",
        "Product": f"Produto {i}",
        "Category": "Geral" if i % 2 == 0 else "Especial",
        "Price": 10.0 + i,
        "Quantity": (i % 5) + 1,
        "Customer Name": f"Cliente {i}",
        "Customer Email": f"cliente{i}@exemplo.com" if i % 3 != 0 else None,
        "Sale Date": (base_date - timedelta(days=30 - i)).strftime("%d/%m/%Y"),
    })

df = pd.DataFrame(rows, columns=cols)

# Save to disk
output_path = "data/sample_data.xlsx"
df.to_excel(output_path, index=False)
print(f"Wrote {output_path}")
