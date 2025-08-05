import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

root = tk.Tk()
root.title("Matrix")
root.iconbitmap('icon.ico')


data = []
default_columns = []

col_input_var = tk.StringVar()
entry_vars = {}
entry_widgets = {}

# --- Frames ---
top_frame = ttk.Frame(root, padding=7)
top_frame.pack(fill='x')

entry_frame = ttk.Frame(root, padding=7)
entry_frame.pack(fill='x')

plot_frame = ttk.Frame(root, padding=7)
plot_frame.pack()

table_frame = ttk.Frame(root)
table_frame.pack(fill='both', expand=True, padx=10, pady=7)

# --- Top Inputs ---
ttk.Label(top_frame, text="Set Default Columns (comma separated):").grid(row=0, column=0, sticky='w')
col_entry = ttk.Entry(top_frame, textvariable=col_input_var, width=50)
col_entry.grid(row=0, column=1, padx=5)
set_button = ttk.Button(top_frame, text="Set Columns")
set_button.grid(row=0, column=2, padx=5)
upload_button = ttk.Button(top_frame, text="Upload CSV")
upload_button.grid(row=0, column=3, padx=5)


table = ttk.Treeview(table_frame, show='headings')
table.pack(fill='both', expand=True)


def set_columns():
    global default_columns
    cols = col_input_var.get().strip()
    if not cols:
        messagebox.showerror("Error", "Please enter at least one column name.")
        return
    columns = [c.strip() for c in cols.split(",") if c.strip()]
    if not columns:
        messagebox.showerror("Error", "Invalid column names.")
        return
    default_columns = columns
    update_table_headings(default_columns)
    col_entry.config(state='disabled')
    set_button.config(state='disabled')
    enable_data_entry_widgets(True)
    data.clear()
    for item in table.get_children():
        table.delete(item)

def update_table_headings(columns):
    table["columns"] = columns
    for col in columns:
        table.heading(col, text=col)
        table.column(col, width=150)
    create_manual_entries(columns)

def create_manual_entries(columns):
    global entry_vars, entry_widgets
    for widget in entry_frame.winfo_children():
        widget.destroy()
    entry_vars = {}
    entry_widgets = {}
    for idx, col in enumerate(columns):
        var = tk.StringVar()
        entry_vars[col] = var
        ttk.Label(entry_frame, text=col).grid(row=0, column=idx*2)
        entry = ttk.Entry(entry_frame, textvariable=var, width=20)
        entry.grid(row=0, column=idx*2 + 1, padx=5)
        entry_widgets[col] = entry
    btn_col = len(columns)*2
    ttk.Button(entry_frame, text="Add Row", command=add_row).grid(row=0, column=btn_col, padx=10)
    ttk.Button(entry_frame, text="Reset", command=reset_data).grid(row=0, column=btn_col+1, padx=5)

def enable_data_entry_widgets(enabled):
    state = 'normal' if enabled else 'disabled'
    for w in entry_frame.winfo_children():
        w.config(state=state)
    for btn in plot_frame.winfo_children():
        btn.config(state=state)

def add_row():
    try:
        row = {}
        for col, var in entry_vars.items():
            val = var.get().strip()
            if val == '':
                raise ValueError(f"Field '{col}' cannot be empty")
            if col != table["columns"][0]:
                try:
                    val = float(val)
                except:
                    raise ValueError(f"Field '{col}' must be numeric")
            row[col] = val
        current_cols = table["columns"]
        if set(current_cols) != set(row.keys()):
            update_table_headings(tuple(row.keys()))
        data.append(row)
        table.insert('', 'end', values=tuple(row[col] for col in current_cols))
        for var in entry_vars.values():
            var.set('')
    except ValueError as ve:
        messagebox.showerror("Invalid Input", str(ve))

def upload_csv():
    filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not filepath:
        return
    try:
        df = pd.read_csv(filepath)
        if df.empty:
            messagebox.showerror("Invalid CSV", "CSV file is empty.")
            return
        columns = list(df.columns)
        global default_columns
        default_columns = columns
        update_table_headings(columns)
        data.clear()
        for item in table.get_children():
            table.delete(item)
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            for col in columns[1:]:
                try:
                    row_dict[col] = float(row_dict[col])
                except:
                    pass
            data.append(row_dict)
            table.insert('', 'end', values=tuple(row_dict.get(col, '') for col in columns))
        col_entry.config(state='disabled')
        set_button.config(state='disabled')
        enable_data_entry_widgets(True)
        col_input_var.set(", ".join(columns))
        messagebox.showinfo("Upload Successful", f"{len(df)} rows loaded from CSV.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load CSV: {e}")

def reset_data():
    if messagebox.askyesno("Confirm Reset", "Clear all data and reset?"):
        data.clear()
        for item in table.get_children():
            table.delete(item)
        col_entry.config(state='normal')
        set_button.config(state='normal')
        col_input_var.set('')
        enable_data_entry_widgets(False)
        table["columns"] = ()

def get_numeric_columns(df):
    return df.select_dtypes(include='number').columns.tolist()

def get_categorical_columns(df):
    return df.select_dtypes(include='object').columns.tolist()

def show_heatmap():
    if len(data) < 2:
        messagebox.showwarning("Not Enough Data", "At least 2 entries needed.")
        return
    df = pd.DataFrame(data)
    num_cols = get_numeric_columns(df)
    cat_cols = get_categorical_columns(df)
    if len(num_cols) < 2:
        messagebox.showerror("Data Error", "Need at least two numeric columns for heatmap.")
        return
    if cat_cols:
        df = df.groupby(cat_cols[0], as_index=False).sum(numeric_only=True)
    plt.figure(figsize=(8, 6))
    sns.heatmap(df[num_cols].corr(), annot=True, cmap='YlGnBu')
    plt.title("Correlation Heatmap (Grouped)")
    plt.tight_layout()
    plt.show()

def show_one_hot_heatmap():
    if len(data) < 2:
        messagebox.showwarning("Not Enough Data", "At least 2 entries needed.")
        return
    df = pd.DataFrame(data)
    cat_cols = get_categorical_columns(df)
    if not cat_cols:
        messagebox.showerror("Data Error", "No categorical column found for one-hot encoding.")
        return
    df_encoded = pd.get_dummies(df, columns=[cat_cols[0]])
    prefix = cat_cols[0] + "_"
    df_encoded.columns = [col[len(prefix):] if col.startswith(prefix) else col for col in df_encoded.columns]

    cat_group = get_categorical_columns(df_encoded)
    if cat_group:
        df_encoded = df_encoded.groupby(cat_group[0], as_index=False).sum(numeric_only=True)

    plt.figure(figsize=(8, 6))
    sns.heatmap(df_encoded.corr(numeric_only=True), annot=False, cmap='YlGnBu')
    plt.title("One-Hot Encoded Heatmap (Grouped)")
    plt.tight_layout()
    plt.show()

def show_scatter():
    df = pd.DataFrame(data)
    if df.empty:
        return
    num_cols = get_numeric_columns(df)
    cat_cols = get_categorical_columns(df)
    if len(num_cols) < 2:
        messagebox.showerror("Data Error", "At least two numeric columns needed for scatter plot.")
        return
    x_col, y_col = num_cols[:2]
    hue_col = cat_cols[0] if cat_cols else None
    if hue_col:
        df = df.groupby(hue_col, as_index=False).sum(numeric_only=True)
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=df, x=x_col, y=y_col, hue=hue_col)
    plt.title(f"Scatter Plot ({x_col} vs {y_col}) - Grouped")
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    if hue_col:
        plt.legend(title=hue_col)
    plt.tight_layout()
    plt.show()

def show_bar():
    df = pd.DataFrame(data)
    if df.empty:
        return
    num_cols = get_numeric_columns(df)
    cat_cols = get_categorical_columns(df)

    if not cat_cols:
        df_bar = df[num_cols]
        df_bar.index = df.index.astype(str)
    else:
        x_col = cat_cols[0]
        df = df.groupby(x_col, as_index=True).sum(numeric_only=True)
        df_bar = df[num_cols]

    plt.figure(figsize=(10, 6))
    df_bar.plot(kind='barh', stacked=True, ax=plt.gca())
    plt.title("Grouped Bar Chart")
    plt.ylabel("Categories")
    plt.xlabel("Values")
    plt.tight_layout()
    plt.show()

def show_column_chart():
    df = pd.DataFrame(data)
    if df.empty:
        return
    num_cols = get_numeric_columns(df)
    cat_cols = get_categorical_columns(df)

    if not num_cols or not cat_cols:
        messagebox.showerror("Data Error", "Need at least one numeric and one categorical column.")
        return

    x_col = cat_cols[0]
    df = df.groupby(x_col, as_index=True).sum(numeric_only=True)
    df_col = df[num_cols]

    plt.figure(figsize=(10, 6))
    df_col.plot(kind='bar', stacked=True, ax=plt.gca())
    plt.title(f"Grouped Column Chart ({x_col})")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Values")
    plt.tight_layout()
    plt.show()

def show_line():
    df = pd.DataFrame(data)
    if df.empty:
        return
    num_cols = get_numeric_columns(df)
    cat_cols = get_categorical_columns(df)

    if cat_cols:
        x_col = cat_cols[0]
        df = df.groupby(x_col, as_index=True).sum(numeric_only=True)
        df_line = df[num_cols]
    else:
        df_line = df[num_cols]
        df_line.index = df.index.astype(str)

    plt.figure(figsize=(10, 6))
    ax = plt.gca()
    df_line.plot(kind='line', marker='o', ax=ax)

    ax.set_xticks(range(len(df_line.index)))
    ax.set_xticklabels(df_line.index, rotation=45, ha='right')

    plt.title("Grouped Line Chart")
    plt.ylabel("Values")
    plt.tight_layout()
    plt.show()



ttk.Button(plot_frame, text="Heatmap", command=show_heatmap).grid(row=0, column=0, padx=5)
ttk.Button(plot_frame, text="One-Hot Heatmap", command=show_one_hot_heatmap).grid(row=0, column=1, padx=5)
ttk.Button(plot_frame, text="Scatter", command=show_scatter).grid(row=0, column=2, padx=5)
ttk.Button(plot_frame, text="Bar", command=show_bar).grid(row=0, column=3, padx=5)
ttk.Button(plot_frame, text="Column", command=show_column_chart).grid(row=0, column=4, padx=5)
ttk.Button(plot_frame, text="Line", command=show_line).grid(row=0, column=5, padx=5)

set_button.config(command=set_columns)
upload_button.config(command=upload_csv)

enable_data_entry_widgets(False)

footer_frame = ttk.Frame(root, padding=7)
footer_frame.pack(fill='x', side='bottom')
ttk.Label(
    footer_frame,
    text="Matrix is developed by Hasan Imam | Contact: hasanimam505@gmail.com",
    font=("Arial", 7),
    foreground="Black"
).pack()

root.mainloop()