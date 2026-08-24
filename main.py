import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


def resource_path(relative_path: str) -> str:
    """获取资源文件路径，兼容 PyInstaller 打包后的运行环境。"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

# 全局映射
items_map = {}      # {"石头": "stone", ...}
enchants_map = {}   # {"锋利": "sharpness", ...}

# ------------------------------------------------------------
# 辅助函数
# ------------------------------------------------------------
def ensure_namespace(id_str: str) -> str:
    """如果 ID 不包含命名空间，自动添加 minecraft: 前缀"""
    id_str = id_str.strip()
    if ':' not in id_str:
        return 'minecraft:' + id_str
    return id_str


def id_to_item_cn(item_id: str) -> str:
    """将物品 ID 转为中文名，找不到时返回原 ID"""
    for cn, iid in items_map.items():
        if ensure_namespace(iid) == item_id:
            return cn
    return item_id


def id_to_enchant_cn(ench_id: str) -> str:
    """将附魔 ID 转为中文名，找不到时返回原 ID"""
    for cn, eid in enchants_map.items():
        if ensure_namespace(eid) == ench_id:
            return cn
    return ench_id


def load_json_with_dialog(default_filename: str) -> dict | None:
    """
    尝试从当前目录加载 JSON；若不存在或格式错误则弹窗让用户选择。
    成功返回 dict，用户取消返回 None。
    """
    path = resource_path(default_filename)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("JSON 根节点应为对象")
            return data
        except Exception as e:
            messagebox.showerror("错误", f"加载 {default_filename} 失败：{e}\n请手动选择文件。")
    # 弹窗选择
    while True:
        path = filedialog.askopenfilename(
            title=f"选择 {default_filename}",
            filetypes=[("JSON 文件", "*.json")]
        )
        if not path:
            return None  # 用户取消
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("JSON 根节点应为对象")
            return data
        except Exception as e:
            messagebox.showerror("错误", f"加载 {path} 失败：{e}")


# ------------------------------------------------------------
# 物品编辑器（用于交易中的单个物品）
# ------------------------------------------------------------
class ItemEditor(ttk.Frame):
    """一个物品及其附魔的编辑区域"""

    def __init__(self, parent, label):
        super().__init__(parent)
        self.label = label
        self.item_var = tk.StringVar()
        self.count_var = tk.IntVar(value=1)
        self.enchant_var = tk.StringVar()
        self.enchant_level_var = tk.IntVar(value=1)
        self.enchants = []  # 每个元素: {"id": "minecraft:sharpness", "lvl": 1, "cn": "锋利"}
        self._create_widgets()

    def _create_widgets(self):
        frame = ttk.LabelFrame(self, text=self.label, padding=5)
        frame.pack(fill='both', expand=True, padx=5, pady=5)

        # 第一行：物品选择 + 数量
        ttk.Label(frame, text="物品:").grid(row=0, column=0, sticky='w')
        self.item_combo = ttk.Combobox(
            frame, textvariable=self.item_var,
            values=list(items_map.keys()), state='normal'
        )
        self.item_combo.grid(row=0, column=1, sticky='we', padx=5)
        ttk.Label(frame, text="数量:").grid(row=0, column=2, sticky='w')
        self.count_spin = ttk.Spinbox(
            frame, from_=1, to=64, textvariable=self.count_var, width=5
        )
        self.count_spin.grid(row=0, column=3, padx=5)

        # 第二行：附魔选择
        ttk.Label(frame, text="附魔:").grid(row=1, column=0, sticky='w')
        self.enchant_combo = ttk.Combobox(
            frame, textvariable=self.enchant_var,
            values=list(enchants_map.keys()), state='normal'
        )
        self.enchant_combo.grid(row=1, column=1, sticky='we', padx=5)
        ttk.Label(frame, text="等级:").grid(row=1, column=2, sticky='w')
        self.enchant_level_spin = ttk.Spinbox(
            frame, from_=1, to=255, textvariable=self.enchant_level_var, width=5
        )
        self.enchant_level_spin.grid(row=1, column=3, padx=5)
        ttk.Button(frame, text="添加附魔", command=self.add_enchant).grid(row=1, column=4, padx=5)

        # 第三行：已添加附魔列表
        self.enchant_listbox = tk.Listbox(frame, height=3)
        self.enchant_listbox.grid(row=2, column=0, columnspan=4, sticky='we', padx=5, pady=5)
        scroll = ttk.Scrollbar(frame, orient='vertical', command=self.enchant_listbox.yview)
        scroll.grid(row=2, column=4, sticky='ns')
        self.enchant_listbox.config(yscrollcommand=scroll.set)
        ttk.Button(frame, text="删除选中附魔", command=self.remove_enchant).grid(
            row=3, column=0, columnspan=2, pady=5
        )
        frame.columnconfigure(1, weight=1)

    def add_enchant(self):
        cn = self.enchant_var.get().strip()
        if not cn:
            messagebox.showerror("错误", "请选择附魔", parent=self)
            return
        if cn not in enchants_map:
            messagebox.showerror("错误", f"未知附魔: {cn}", parent=self)
            return
        ench_id = ensure_namespace(enchants_map[cn])
        # 检查重复
        for e in self.enchants:
            if e['id'] == ench_id:
                messagebox.showerror("错误", f"附魔 {cn} 已存在", parent=self)
                return
        try:
            lvl = int(self.enchant_level_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("错误", "附魔等级必须为整数", parent=self)
            return
        if lvl <= 0:
            messagebox.showerror("错误", "附魔等级必须为正整数", parent=self)
            return
        self.enchants.append({"id": ench_id, "lvl": lvl, "cn": cn})
        self.refresh_enchant_list()
        self.enchant_var.set('')
        self.enchant_level_var.set(1)

    def remove_enchant(self):
        sel = self.enchant_listbox.curselection()
        if not sel:
            messagebox.showerror("错误", "请选择要删除的附魔", parent=self)
            return
        idx = sel[0]
        del self.enchants[idx]
        self.refresh_enchant_list()

    def refresh_enchant_list(self):
        self.enchant_listbox.delete(0, tk.END)
        for e in self.enchants:
            self.enchant_listbox.insert(tk.END, f"{e['cn']} (等级 {e['lvl']})")

    def set_data(self, item_id, count, enchants):
        """填充已有数据（用于修改模式）"""
        cn = id_to_item_cn(item_id)
        self.item_var.set(cn)
        self.count_var.set(count)
        self.enchants = []
        for e in enchants:
            cn_e = id_to_enchant_cn(e['id'])
            self.enchants.append({"id": e['id'], "lvl": e['lvl'], "cn": cn_e})
        self.refresh_enchant_list()

    def get_data(self):
        """验证并返回 (item_id, count, enchants) 或 None"""
        cn = self.item_var.get().strip()
        if cn not in items_map:
            messagebox.showerror("错误", f"未知物品: {cn}", parent=self)
            return None
        item_id = ensure_namespace(items_map[cn])
        try:
            count = int(self.count_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("错误", "物品数量必须为整数", parent=self)
            return None
        if count <= 0:
            messagebox.showerror("错误", "物品数量必须为正整数", parent=self)
            return None
        enchants = [{"id": e['id'], "lvl": e['lvl']} for e in self.enchants]
        return (item_id, count, enchants)

    def set_enabled(self, enabled: bool):
        """递归启用/禁用所有子控件"""
        state = 'normal' if enabled else 'disabled'
        self._set_widget_state(self, state)

    def _set_widget_state(self, widget, state):
        try:
            widget.configure(state=state)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_widget_state(child, state)


# ------------------------------------------------------------
# 交易编辑对话框
# ------------------------------------------------------------
class TradeDialog(tk.Toplevel):
    def __init__(self, parent, trade=None):
        super().__init__(parent)
        self.title("添加交易" if trade is None else "修改交易")
        self.result = None
        self.transient(parent)
        self.grab_set()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # 购买物品1
        self.buy_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.buy_tab, text="购买物品1")
        self.buy_editor = ItemEditor(self.buy_tab, "购买物品1")
        self.buy_editor.pack(fill='both', expand=True)

        # 购买物品2（可选）
        self.buyB_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.buyB_tab, text="购买物品2（可选）")
        self.enable_buyB_var = tk.BooleanVar(value=False)
        self.buyB_check = ttk.Checkbutton(
            self.buyB_tab, text="启用购买物品2",
            variable=self.enable_buyB_var,
            command=self.toggle_buyB
        )
        self.buyB_check.pack(anchor='w', padx=5, pady=2)
        self.buyB_editor = ItemEditor(self.buyB_tab, "购买物品2")
        self.buyB_editor.pack(fill='both', expand=True)
        self.toggle_buyB()

        # 出售物品
        self.sell_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.sell_tab, text="出售物品")
        self.sell_editor = ItemEditor(self.sell_tab, "出售物品")
        self.sell_editor.pack(fill='both', expand=True)

        # 交易选项
        self.option_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.option_tab, text="交易选项")
        ttk.Label(self.option_tab, text="最大交易次数 (maxUses):").pack(anchor='w', padx=5, pady=5)
        self.maxUses_var = tk.IntVar(value=12)
        ttk.Spinbox(
            self.option_tab, from_=1, to=9999,
            textvariable=self.maxUses_var, width=10
        ).pack(anchor='w', padx=5)

        # 底部按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text="保存", command=self.save).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy).pack(side='right', padx=5)

        if trade is not None:
            self.load_trade(trade)

        self.geometry("480x500")

    def toggle_buyB(self):
        self.buyB_editor.set_enabled(self.enable_buyB_var.get())

    def load_trade(self, trade):
        self.buy_editor.set_data(trade['buy']['item'], trade['buy']['count'], trade['buy'].get('enchants', []))
        self.sell_editor.set_data(trade['sell']['item'], trade['sell']['count'], trade['sell'].get('enchants', []))
        if 'buyB' in trade:
            self.enable_buyB_var.set(True)
            self.buyB_editor.set_data(trade['buyB']['item'], trade['buyB']['count'], trade['buyB'].get('enchants', []))
            self.toggle_buyB()
        self.maxUses_var.set(trade.get('maxUses', 12))

    def save(self):
        buy_data = self.buy_editor.get_data()
        if buy_data is None:
            return
        sell_data = self.sell_editor.get_data()
        if sell_data is None:
            return

        try:
            max_uses = int(self.maxUses_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("错误", "最大交易次数必须为整数", parent=self)
            return
        if max_uses <= 0:
            messagebox.showerror("错误", "最大交易次数必须为正整数", parent=self)
            return

        trade = {
            'buy': {
                'item': buy_data[0],
                'count': buy_data[1],
                'enchants': buy_data[2],
            },
            'sell': {
                'item': sell_data[0],
                'count': sell_data[1],
                'enchants': sell_data[2],
            },
            'maxUses': max_uses,
        }

        if self.enable_buyB_var.get():
            buyB_data = self.buyB_editor.get_data()
            if buyB_data is None:
                return
            trade['buyB'] = {
                'item': buyB_data[0],
                'count': buyB_data[1],
                'enchants': buyB_data[2],
            }

        self.result = trade
        self.destroy()


# ------------------------------------------------------------
# 主程序
# ------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MC自定义交易村民生成器")
        self.geometry("900x650")
        self.trades = []
        self.load_json_files()
        self.create_widgets()
        self.refresh_trade_list()

    # ---------- 数据加载 ----------
    def load_json_files(self):
        global items_map, enchants_map
        items_map = load_json_with_dialog("MCitems.json") or {}
        enchants_map = load_json_with_dialog("MCenchants.json") or {}
        if not items_map or not enchants_map:
            messagebox.showwarning(
                "警告",
                "物品或附魔映射未加载完整，部分功能可能受限。\n可通过“重新加载JSON”按钮重新加载。"
            )

    def reload_json(self):
        self.load_json_files()
        self.refresh_trade_list()
        messagebox.showinfo("提示", "JSON 重新加载完成，新建的编辑对话框将使用新映射。")

    # ---------- 界面构建 ----------
    def create_widgets(self):
        # 顶部按钮
        top_frame = ttk.Frame(self)
        top_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(top_frame, text="重新加载JSON", command=self.reload_json).pack(side='left')
        ttk.Button(top_frame, text="添加交易", command=self.add_trade).pack(side='left', padx=5)
        ttk.Button(top_frame, text="修改选中交易", command=self.modify_trade).pack(side='left', padx=5)
        ttk.Button(top_frame, text="删除选中交易", command=self.delete_trade).pack(side='left')

        # 交易列表
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        columns = ('index', 'buy', 'buyB', 'sell', 'uses')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        self.tree.heading('index', text='序号')
        self.tree.column('index', width=50, anchor='center')
        self.tree.heading('buy', text='购买物品')
        self.tree.column('buy', width=250)
        self.tree.heading('buyB', text='购买物品2')
        self.tree.column('buyB', width=200)
        self.tree.heading('sell', text='出售物品')
        self.tree.column('sell', width=250)
        self.tree.heading('uses', text='最大次数')
        self.tree.column('uses', width=80, anchor='center')
        self.tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.tree.config(yscrollcommand=scrollbar.set)

        # 村民选项
        option_frame = ttk.Frame(self)
        option_frame.pack(fill='x', padx=5, pady=5)
        self.no_ai_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            option_frame, text="村民不可移动 (NoAI)",
            variable=self.no_ai_var
        ).pack(side='left')

        # 生成按钮
        ttk.Button(option_frame, text="生成指令并复制", command=self.generate).pack(side='right')

        # 指令输出
        output_frame = ttk.LabelFrame(self, text="生成的指令")
        output_frame.pack(fill='both', expand=True, padx=5, pady=5)
        self.command_text = tk.Text(output_frame, height=6, wrap='word')
        self.command_text.pack(fill='both', expand=True, padx=5, pady=5)

    # ---------- 交易列表刷新 ----------
    def describe_item(self, item):
        cn = id_to_item_cn(item['item'])
        s = f"{cn} x{item['count']}"
        if item.get('enchants'):
            ench_str = ', '.join([f"{id_to_enchant_cn(e['id'])} {e['lvl']}" for e in item['enchants']])
            s += f" [{ench_str}]"
        return s

    def refresh_trade_list(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for i, trade in enumerate(self.trades):
            buy_str = self.describe_item(trade['buy'])
            buyB_str = self.describe_item(trade['buyB']) if 'buyB' in trade else '-'
            sell_str = self.describe_item(trade['sell'])
            uses = trade.get('maxUses', 12)
            self.tree.insert('', 'end', iid=str(i), values=(i + 1, buy_str, buyB_str, sell_str, uses))

    # ---------- 交易操作 ----------
    def add_trade(self):
        if not items_map or not enchants_map:
            messagebox.showerror("错误", "请先加载物品和附魔 JSON 文件")
            return
        dialog = TradeDialog(self)
        self.wait_window(dialog)
        if dialog.result is not None:
            self.trades.append(dialog.result)
            self.refresh_trade_list()

    def modify_trade(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("错误", "请先选中一个交易")
            return
        idx = int(selection[0])
        dialog = TradeDialog(self, self.trades[idx])
        self.wait_window(dialog)
        if dialog.result is not None:
            self.trades[idx] = dialog.result
            self.refresh_trade_list()

    def delete_trade(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("错误", "请先选中一个交易")
            return
        idx = int(selection[0])
        del self.trades[idx]
        self.refresh_trade_list()

    # ---------- 生成指令 ----------
    def generate(self):
        if not self.trades:
            messagebox.showerror("错误", "请至少添加一个交易")
            return
        command = self.build_command()
        self.command_text.delete('1.0', tk.END)
        self.command_text.insert('1.0', command)
        self.clipboard_clear()
        self.clipboard_append(command)
        messagebox.showinfo("成功", "指令已生成并复制到剪贴板")

    def build_command(self):
        def item_to_snbt(item):
            s = f'{{id:"{item["item"]}",Count:{item["count"]}b'
            if item.get('enchants'):
                ench = ','.join([f'{{id:"{e["id"]}",lvl:{e["lvl"]}s}}' for e in item['enchants']])
                s += f',tag:{{Enchantments:[{ench}]}}'
            s += '}'
            return s

        recipes = []
        for trade in self.trades:
            parts = [f'buy:{item_to_snbt(trade["buy"])}']
            if 'buyB' in trade:
                parts.append(f'buyB:{item_to_snbt(trade["buyB"])}')
            parts.append(f'sell:{item_to_snbt(trade["sell"])}')
            parts.append(f'maxUses:{trade.get("maxUses", 12)}')
            parts.append('rewardExp:1b')
            recipes.append('{' + ','.join(parts) + '}')
        recipes_str = ','.join(recipes)
        no_ai = 1 if self.no_ai_var.get() else 0
        command = (
            f'/summon minecraft:villager ~ ~ ~ '
            f'{{VillagerData:{{profession:"minecraft:farmer",level:1,type:"minecraft:plains"}},'
            f'NoAI:{no_ai}b,Offers:{{Recipes:[{recipes_str}]}}}}'
        )
        return command


# ------------------------------------------------------------
# 入口
# ------------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()
