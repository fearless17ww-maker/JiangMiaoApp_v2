import flet as ft
import json
import time
import datetime
import calendar
import asyncio
import random

# ================= 兼容性补丁 (开始) =================
# 自动检测环境：如果你本地是旧版 Flet，自动适配组件名
if not hasattr(ft, "NavigationDestination"):
    ft.NavigationDestination = ft.NavigationBarDestination
# ================= 兼容性补丁 (结束) =================

# --- 颜色配置 ---
COLOR_PINK_BG = "#FFF0F5"       # 淡粉色背景
COLOR_PINK_ACCENT = "#FFB6C1"   # 浅粉红
COLOR_YELLOW = "#FFFACD"        # 柠檬绸色
COLOR_TEXT = "#5D4037"          # 深褐色
COLOR_DONE = "#E0E0E0"          # 灰色
DATA_FILE = "persistence.json"

# 高区分度色板
HABIT_PALETTE = [
    "#FF5252", "#448AFF", "#00C853", "#FFAB00", "#AA00FF", 
    "#00BCD4", "#FF4081", "#795548", "#607D8B", "#212121", 
]

class PersistenceApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "JiangMiao"
        self.page.bgcolor = COLOR_PINK_BG
        self.page.padding = 0
        # 使用 Material 3 风格
        self.page.theme = ft.Theme(color_scheme_seed="pink", use_material3=True)
        
        # 初始化数据
        self.data = self.load_data()
        
        # --- UI 组件初始化 ---
        
        # 1. 底部导航栏
        # 【修改点】：图标全部改成字符串，兼容所有版本
        self.nav_bar = ft.NavigationBar(
            selected_index=1,
            on_change=self.on_tab_change,
            bgcolor="white",
            destinations=[
                # index 0: 统计
                ft.NavigationDestination(
                    icon="bar_chart_outlined",      # 使用字符串
                    selected_icon="bar_chart",      # 使用字符串
                    label="统计"
                ),
                # index 1: 今日坚持
                ft.NavigationDestination(
                    icon="check_circle_outline",    # 使用字符串
                    selected_icon="check_circle",   # 使用字符串
                    label="打卡",
                ),
                # index 2: 日历
                ft.NavigationDestination(
                    icon="calendar_month_outlined", # 使用字符串
                    selected_icon="calendar_month", # 使用字符串
                    label="日历"
                ),
            ]
        )

        # 2. 悬浮按钮 (FAB)
        self.fab = ft.FloatingActionButton(
            icon="add",  # 使用字符串
            bgcolor=COLOR_PINK_ACCENT,
            on_click=self.open_add_dialog,
            shape=ft.CircleBorder(),
        )

        # 3. 内容容器
        self.content_container = ft.Container(
            expand=True,
            padding=10
        )

        self.show_splash()

    def load_data(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for h in data.get("habits", []):
                    if "color" not in h:
                        h["color"] = random.choice(HABIT_PALETTE)
                return data
        except:
            return {
                "habits": [
                    {"name": "健身", "target": "30分钟有氧", "color": "#FF5252"},
                    {"name": "练琴", "target": "哈农练习第1条", "color": "#448AFF"},
                    {"name": "英语口语", "target": "跟读一篇VOA", "color": "#00C853"}
                ],
                "history": {} 
            }

    def save_data(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    # --- 1. 载入动画 ---
    def show_splash(self):
        img_src = "assets/cover.png" 
        
        splash_content = ft.Container(
            alignment=ft.alignment.center,
            bgcolor=COLOR_PINK_ACCENT,
            expand=True,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                controls=[
                    ft.Image(src=img_src, width=150, height=150, fit=ft.ImageFit.CONTAIN, border_radius=75),
                    ft.Container(
                        width=self.page.width * 0.66 if self.page.width else 300, 
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=5,
                            controls=[
                                ft.Text("坚持每一天", size=40, color="white", weight=ft.FontWeight.BOLD, font_family="Verdana", text_align="center"),
                                ft.Text("jiang小喵支持你！", size=24, color="white", weight=ft.FontWeight.BOLD, text_align="center"),
                            ]
                        )
                    ),
                    ft.ProgressRing(color="white"),
                ]
            )
        )
        
        self.page.add(splash_content)
        self.page.update()
        time.sleep(1.5)
        self.page.controls.clear()
        self.init_main_ui()

    # --- 2. 主界面架构 ---
    def init_main_ui(self):
        self.page.navigation_bar = self.nav_bar 
        self.page.floating_action_button = self.fab 
        
        # 使用 SafeArea
        self.page.add(
            ft.SafeArea(
                content=ft.Column(
                    expand=True,
                    controls=[
                        self.content_container
                    ]
                )
            )
        )
        self.render_home()

    def on_tab_change(self, e):
        index = e.control.selected_index
        self.page.floating_action_button.visible = (index == 1)
        self.page.update()

        if index == 0:
            self.render_stats()
        elif index == 1:
            self.render_home()
        elif index == 2:
            self.render_calendar()

    # --- 3. 首页渲染 ---
    def render_home(self):
        today = str(datetime.date.today())
        history = self.data["history"].get(today, [])
        habits = self.data["habits"]

        controls_list = []

        controls_list.append(
            ft.Container(
                bgcolor=COLOR_YELLOW,
                padding=15,
                border_radius=20,
                content=ft.Text("今日任务", size=20, weight="bold", color=COLOR_TEXT, text_align="center"),
                alignment=ft.alignment.center,
                margin=ft.margin.only(bottom=10)
            )
        )

        controls_list.append(ft.Text("待完成", color="grey500"))
        
        for habit in habits:
            if habit['name'] not in history:
                controls_list.append(self.create_habit_card(habit, is_done=False))

        controls_list.append(ft.Divider(height=20, color="transparent"))
        controls_list.append(ft.Text("已完成", color="grey500"))

        for habit in habits:
            if habit['name'] in history:
                controls_list.append(self.create_habit_card(habit, is_done=True))
        
        controls_list.append(ft.Container(height=100))

        self.content_container.content = ft.Column(
            expand=True,
            spacing=10,
            controls=controls_list,
            scroll=ft.ScrollMode.ALWAYS
        )
        self.page.update()

    # --- 4. 创建卡片 ---
    def create_habit_card(self, habit_data, is_done):
        name = habit_data['name']
        target = habit_data['target']
        color = habit_data.get('color', COLOR_PINK_ACCENT)

        def on_long_press_card(e):
            def confirm_delete(e):
                self.data['habits'] = [h for h in self.data['habits'] if h['name'] != name]
                history = self.data['history']
                for date_key in list(history.keys()):
                    if name in history[date_key]:
                        history[date_key].remove(name)
                
                self.save_data()
                self.page.close(dlg)
                self.render_home()

            dlg = ft.AlertDialog(
                title=ft.Text("删除确认"),
                content=ft.Text(f"确定要删除「{name}」吗？\n相关记录也将被清除。"),
                actions=[
                    ft.TextButton("取消", on_click=lambda e: self.page.close(dlg)),
                    ft.TextButton("删除", on_click=confirm_delete, style=ft.ButtonStyle(color="red")),
                ],
            )
            self.page.open(dlg)

        async def on_click_card(e):
            ctr = e.control
            ctr.opacity = 0
            ctr.scale = 0.9
            ctr.update()
            await asyncio.sleep(0.4)
            if is_done:
                self.unmark_done(name)
            else:
                self.mark_done(name)

        container = ft.Container(
            bgcolor="white" if not is_done else COLOR_DONE,
            border_radius=20,
            padding=15,
            animate=ft.Animation(400, "easeOut"), 
            animate_opacity=300,
            animate_scale=300,
            on_click=on_click_card, 
            on_long_press=on_long_press_card,
            ink=True, 
            content=ft.Row(
                controls=[
                    ft.Container(width=8, height=45, bgcolor=color if not is_done else "grey", border_radius=4),
                    ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            ft.Text(name, size=18, weight="bold", color=COLOR_TEXT if not is_done else "grey"),
                            ft.Text(f"目标: {target}", size=12, color="grey")
                        ]
                    ),
                    # 【修改点】：使用字符串 "check_circle"
                    ft.Icon(
                        name="check_circle" if is_done else "radio_button_unchecked",
                        color=color if is_done else "grey400"
                    )
                ]
            )
        )
        return container

    def mark_done(self, name):
        today = str(datetime.date.today())
        if today not in self.data["history"]:
            self.data["history"][today] = []
        if name not in self.data["history"][today]:
            self.data["history"][today].append(name)
            self.save_data()
        self.render_home()
        self.check_all_complete()

    def unmark_done(self, name):
        today = str(datetime.date.today())
        if today in self.data["history"]:
            if name in self.data["history"][today]:
                self.data["history"][today].remove(name)
                self.save_data()
                self.render_home()

    def check_all_complete(self):
        today = str(datetime.date.today())
        history = self.data["history"].get(today, [])
        all_habits = [h['name'] for h in self.data['habits']]
        if all(h in history for h in all_habits) and len(all_habits) > 0:
            dlg = ft.AlertDialog(
                title=ft.Text("太棒啦！"),
                content=ft.Text("jiang小喵知道你一定能行！\n今日任务全部达成！"),
                actions=[ft.TextButton("开心收下", on_click=lambda e: self.page.close(dlg))],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.open(dlg)

    def open_add_dialog(self, e):
        name_field = ft.TextField(label="习惯名称 (如: 喝水)")
        target_field = ft.TextField(label="目标 (如: 8杯)")
        
        def close_dlg(e):
            self.page.close(dlg)

        def add_task(e):
            if name_field.value:
                new_color = random.choice(HABIT_PALETTE)
                self.data['habits'].append({
                    "name": name_field.value,
                    "target": target_field.value,
                    "color": new_color
                })
                self.save_data()
                self.render_home()
                self.page.close(dlg)

        dlg = ft.AlertDialog(
            title=ft.Text("添加新坚持"),
            content=ft.Column([name_field, target_field], height=150),
            actions=[
                ft.TextButton("取消", on_click=close_dlg),
                ft.TextButton("添加", on_click=add_task),
            ],
        )
        self.page.open(dlg)

    # --- 5. 统计页面 ---
    def render_stats(self):
        stats = {}
        history = self.data["history"]
        current_habits_names = [h['name'] for h in self.data['habits']]
        
        for date_str, done_list in history.items():
            for item in done_list:
                if item in current_habits_names:
                    stats[item] = stats.get(item, 0) + 1
        
        controls = []
        controls.append(ft.Text("坚持记录", size=24, weight="bold", color=COLOR_TEXT, text_align="center"))
        
        for h in self.data["habits"]:
            name = h['name']
            count = stats.get(name, 0)
            color = h.get("color", COLOR_PINK_ACCENT)
            
            controls.append(
                ft.Container(
                    bgcolor="white",
                    padding=20,
                    border_radius=15,
                    content=ft.Row([
                        ft.Row([
                            ft.Container(width=10, height=10, bgcolor=color, border_radius=5),
                            ft.Text(name, size=16, weight="bold"),
                        ]),
                        ft.Text(f"累计 {count} 天", color=color, weight="bold")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                )
            )
        
        self.content_container.content = ft.Column(
            expand=True,
            controls=controls,
            spacing=10,
            scroll=ft.ScrollMode.ALWAYS
        )
        self.page.update()

    # --- 6. 日历页面 ---
    def render_calendar(self):
        today = datetime.date.today()
        cal = calendar.monthcalendar(today.year, today.month)
        weeks = ft.Row([ft.Text(d, width=40, text_align="center", size=12, color="grey") for d in ["一","二","三","四","五","六","日"]], alignment=ft.MainAxisAlignment.CENTER)
        
        grid_col = ft.Column(controls=[
            ft.Text(f"{today.year}年{today.month}月", size=20, weight="bold", text_align="center"),
            weeks
        ], spacing=10)

        history = self.data["history"]
        habit_color_map = {h['name']: h.get('color', COLOR_PINK_ACCENT) for h in self.data['habits']}
        current_habits_names = list(habit_color_map.keys())

        for week in cal:
            row = ft.Row(alignment=ft.MainAxisAlignment.CENTER)
            for day in week:
                if day == 0:
                    row.controls.append(ft.Container(width=42, height=50))
                else:
                    date_str = f"{today.year}-{today.month:02d}-{day:02d}" 
                    key = str(datetime.date(today.year, today.month, day))
                    raw_done_items = history.get(key, [])
                    done_items = [item for item in raw_done_items if item in current_habits_names]
                    
                    dots_row = ft.Row(wrap=True, spacing=2, run_spacing=2, alignment=ft.MainAxisAlignment.CENTER, width=38)
                    for item_name in done_items:
                        item_color = habit_color_map.get(item_name, "grey")
                        dots_row.controls.append(ft.Container(width=5, height=5, bgcolor=item_color, border_radius=2.5))
                    
                    is_today = (key == str(today))
                    day_container = ft.Container(
                        content=ft.Column(
                            spacing=2,
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Text(str(day), color=COLOR_PINK_ACCENT if is_today else COLOR_TEXT, weight="bold" if is_today else "normal", size=14),
                                dots_row
                            ]
                        ),
                        width=42, height=50, bgcolor="white", border_radius=8,
                        border=ft.border.all(1.5, COLOR_PINK_ACCENT) if is_today else None
                    )
                    row.controls.append(day_container)
            grid_col.controls.append(row)
            
        self.content_container.content = ft.Column(
            expand=True,
            controls=[grid_col],
            scroll=ft.ScrollMode.ALWAYS
        )
        self.page.update()

def main(page: ft.Page):
    app = PersistenceApp(page)

ft.app(target=main)