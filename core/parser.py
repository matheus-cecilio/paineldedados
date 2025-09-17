import pandas as pd
from difflib import get_close_matches

COMMON_COLUMNS = {
    'product': ['product', 'produto', 'item', 'description', 'produto_nome', 'nome_produto'],
    'quantity': ['quantity', 'qty', 'quantidade', 'qtd'],
    'unit_price': ['unit_price', 'price', 'preco', 'preco_unitario', 'valor unitário','valor_unitario', 'valor'],
    'date': ['date', 'data', 'data_venda'],
    'invoice_number': ['invoice', 'invoice_number', 'numero_nota', 'nota', 'nf', 'numero_fatura'],
    'customer': ['customer', 'client', 'cliente', 'buyer', 'nome_cliente', 'cliente_nome'],
    'sku': ['sku', 'codigo', 'codigo_produto', 'sku_produto'],
    'total': ['total value', 'valor total', 'total', 'valor_total']
}
    
def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df

def detect_mapping(df):
    df2 = normalize_columns(df)
    cols = df2.columns.tolist()
    mapping = {}
    for target, variants in COMMON_COLUMNS.items():
        for v in variants:
            if v in cols:
                mapping[target] = v
                break
        else:
            match = get_close_matches(target, cols, n=1)
            if match:
                mapping[target] = match[0]
    return mapping

def parse_sales_dataframe(df, mapping=None):
    df = normalize_columns(df)
    if mapping is None:
        mapping = detect_mapping(df)
    missing = [k for k in ('product','quantity','unit_price') if k not in mapping]
    if missing:
        raise ValueError(f'Colunas obrigatórias não encontradas: {missing}')
    out = pd.DataFrame()
    out['produto'] = df[mapping['product']]
    out['quantidade'] = pd.to_numeric(df[mapping['quantity']], errors='coerce').fillna(0)
    out['preco_unitario'] = pd.to_numeric(df[mapping['unit_price']], errors='coerce').fillna(0.0)
    out['cliente'] = df[mapping['customer']].fillna('Cliente') if 'customer' in mapping else 'Cliente'
    out['numero_nota'] = df[mapping['invoice_number']].astype(str) if 'invoice_number' in mapping else None
    if 'date' in mapping:
        date_formats = ['%d/%m/%Y','%d-%m-%Y','%Y-%m-%d','%Y/%m/%d','%d/%m/%y','%d-%m-%y']
        out['data'] = pd.NaT
        for fmt in date_formats:
            try:
                temp = pd.to_datetime(df[mapping['date']], format=fmt, errors='coerce')
                out['data'] = out['data'].fillna(temp)
            except: continue
        if out['data'].isna().any():
            out['data'] = pd.to_datetime(df[mapping['date']], errors='coerce')
    else:
        out['data'] = pd.NaT
    return out, mapping
