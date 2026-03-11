import flet as ft
import requests
import math
import json
import os

AGENCY_NAME = "Skypedia"
DATA_FILE = "Save Date.json"

def main(page: ft.Page):
    page.title = f"{AGENCY_NAME} - Professional System"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 900
    page.window_height = 950
    page.scroll = "adaptive"
    page.padding = 30

    origin_coords = {"val": None}
    dest_data = {"val": None}
    records = []

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                records = json.load(f)
        except:
            records = []

    origin_input = ft.TextField(label="Step 1: Origin Country", hint_text="enter your origin country", expand=True)
    dest_input = ft.TextField(label="Step 2: Destination Country", hint_text="enter your destination country", expand=True)
    client_name = ft.TextField(label="Client Name", width=250)
    stay_days = ft.TextField(label="Days", width=100, keyboard_type=ft.KeyboardType.NUMBER)
    travel_date = ft.TextField(label="Travel Date", hint_text="YYYY-MM-DD", width=200)

    info_display = ft.Column(spacing=15)
    history_list = ft.ListView(expand=1, spacing=10, padding=10, height=200)

    def update_history_ui():
        history_list.controls.clear()
        for r in reversed(records):
            history_list.controls.append(
                ft.ListTile(
                    title=ft.Text(f"{r.get('client')}: {r.get('from')} -> {r.get('to')}"),
                    subtitle=ft.Text(f"Date: {r.get('date')} | Cost: {r.get('cost')}"),
                    bgcolor="#f0f2f5", 
                )
            )
        history_list.update()
        page.update()

    def set_origin(e):
        name = origin_input.value.strip()
        if not name: return
        try:
            res = requests.get(f"https://restcountries.com/v3.1/name/{name}")
            results = res.json()
            data = results[0]
            for c in results:
                if c['name']['common'].lower() == name.lower():
                    data = c
                    break
            origin_coords["val"] = data['latlng']
            page.snack_bar = ft.SnackBar(ft.Text(f"Origin confirmed: {data['name']['common']}"))
            page.snack_bar.open = True
            page.update()
        except: pass

    def get_destination_data(e):
        name = dest_input.value.strip()
        if not name: return
        try:
            res = requests.get(f"https://restcountries.com/v3.1/name/{name}")
            results = res.json()
            
            data = results[0]
            for c in results:
                if c['name']['common'].lower() == name.lower():
                    data = c
                    break
            
            dest_data["val"] = data
            
            official_name = data.get('name', {}).get('official', 'N/A')
            capital = data.get('capital', ['N/A'])[0]
            region = f"{data.get('region', 'N/A')} ({data.get('subregion', 'N/A')})"
            population = f"{data.get('population', 0):,}"
            
            curr_str = ", ".join([f"{v.get('name')} ({v.get('symbol')})" for k, v in data.get('currencies', {}).items()])
            lang_str = ", ".join([v for k, v in data.get('languages', {}).items()])
            timezone = ", ".join(data.get('timezones', ['N/A'])[:2])

            lat, lon = data['latlng']
            w_res = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true").json()
            temp = w_res['current_weather']['temperature']

            info_display.controls.clear()
            info_display.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Image(src=data['flags']['png'], width=150, border_radius=10),
                            ft.Column([
                                ft.Text(official_name, weight="bold", size=22, color="#1a237e"),
                                ft.Text(f"Capital: {capital}", size=16),
                            ], expand=True)
                        ]),
                        ft.Divider(),
                        ft.ResponsiveRow([
                            ft.Column([ft.Text("Region", weight="bold"), ft.Text(region)], col={"sm": 6, "md": 4}),
                            ft.Column([ft.Text("Population", weight="bold"), ft.Text(population)], col={"sm": 6, "md": 4}),
                            ft.Column([ft.Text("Currency", weight="bold"), ft.Text(curr_str)], col={"sm": 6, "md": 4}),
                        ]),
                        ft.ResponsiveRow([
                            ft.Column([ft.Text("Languages", weight="bold"), ft.Text(lang_str)], col={"sm": 6, "md": 4}),
                            ft.Column([ft.Text("Time Zones", weight="bold"), ft.Text(timezone)], col={"sm": 6, "md": 4}),
                            ft.Column([ft.Text("Current Weather", weight="bold"), ft.Text(f"{temp}C", color="#2196f3", size=18)], col={"sm": 6, "md": 4}),
                        ]),
                    ]),
                    padding=10,
                    bgcolor="#ffffff",
                    border_radius=10
                )
            )
            page.update()
        except: pass

    def save_plan(e):
        if not origin_coords["val"] or not dest_data["val"]:
            page.snack_bar = ft.SnackBar(ft.Text("Error: Set origin and destination first!"))
            page.snack_bar.open = True
            page.update()
            return

        lat1, lon1 = origin_coords["val"]
        lat2, lon2 = dest_data["val"]['latlng']
        dist = math.sqrt((lat2-lat1)**2 + (lon2-lon1)**2) * 111
        
        try:
            days = int(stay_days.value) if stay_days.value else 0
            total_cost = round((dist * 0.12) + (days * 150) + 200, 2)
            
            entry = {
                "client": client_name.value,
                "from": origin_input.value,
                "to": dest_data["val"]['name']['common'],
                "date": travel_date.value,
                "cost": f"${total_cost}"
            }
            records.append(entry)
            with open(DATA_FILE, 'w') as f:
                json.dump(records, f, indent=4)
            
            update_history_ui()
            page.snack_bar = ft.SnackBar(ft.Text("Success: Itinerary saved!"))
            page.snack_bar.open = True
        except: pass
        page.update()

    page.add(
        ft.Column([
            ft.Row([ft.Text(AGENCY_NAME, size=32, weight="bold", color="#1a237e")], 
                   alignment=ft.MainAxisAlignment.CENTER),
            ft.Card(
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Row([origin_input, ft.ElevatedButton("Confirm Origin", on_click=set_origin)]),
                        ft.Row([dest_input, ft.ElevatedButton("Search Destination", on_click=get_destination_data)]),
                    ])
                )
            ),
            info_display,
            ft.Card(
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Text("Step 3: Booking Details", weight="bold", size=18),
                        ft.Row([client_name, stay_days, travel_date]),
                        ft.ElevatedButton("Save & Calculate Cost", 
                                         on_click=save_plan, 
                                         width=900,
                                         bgcolor="#4caf50", color="white")
                    ])
                )
            ),
            ft.Text("Recent Bookings", size=20, weight="bold"),
            history_list,
            ft.Text("Founded in 2026 | Crew: Haochen Huang, Mark Lin, Paolo Dal Cin", size=12, color="grey")
        ], spacing=20)
    )

    update_history_ui()

if __name__ == "__main__":
    ft.app(target=main)