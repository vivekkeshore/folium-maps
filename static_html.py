from datetime import datetime

now = datetime.now()

title_html = f"""
<div style="position: fixed; top: 8px; left: 50%; transform: translateX(-50%);
			background: white; padding: 12px 22px; border-radius: 12px;
			box-shadow: 0 5px 15px rgba(0,0,0,0.4); z-index: 9999; font-family: Arial; text-align:center;">
    <h3 style="margin:0; color:#b71c1c; font-size:21px;">📍 Iran–Israel–USA Conflict 2026 ({now.strftime('%b')} {now.strftime('%d')} Update)</h3>
    <p style="margin:6px 0 0 0; font-size:14px; color:#333;">
        🟥 Red = Israel/US strikes (incl. torpedo strike (Indian Ocean)) | 🟦 Blue = Iranian retaliation<br>
        🔥 Heatmaps | 🚀 Animated Missile Trails | ⏱️ Time-Slider (Feb 28 – {now.strftime('%b')} {now.strftime('%d')})
    </p>
</div>
"""
# Add a legend/list of countries involved (floating text box)
countries_list_html = f"""
<div style="position: fixed; bottom: 20px; right: 20px; background: white; padding: 15px; border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4); z-index: 1000; font-family: Arial; max-width: 380px; overflow-y: auto; max-height: 60vh;">
    <h4 style="margin:0 0 10px 0; color:#b71c1c;">Countries Involved in the Conflict (as of {now.strftime('%b')} {now.strftime('%d')}, 2026)</h4>
    <ul style="margin:0; padding-left:20px; font-size:13px; line-height:1.5;">
        <li><b>Direct Belligerents:</b> Iran (primary target/retaliator), United States (leading strikes/Operation Epic Fury), Israel (co-leading attacks/regime change goal)</li>
        <li><b>US Bases/Targets Hit by Iran:</b> Qatar (Al Udeid), Bahrain (5th Fleet HQ + desalination), UAE (Al Dhafra + oil port), Kuwait (Camp Arifjan + civilian), Saudi Arabia (Riyadh facilities + oil), Jordan (US/THAAD sites), Iraq (Baghdad/US positions)</li>
        <li><b>Proxy/Active Fronts:</b> Lebanon (Hezbollah launching on Israel; Israeli ground invasion south/Beirut/Beqaa; heavy casualties)</li>
        <li><b>Other Strikes by Iran:</b> Azerbaijan (drones/missiles; airspace closed), Cyprus (UK RAF Akrotiri/Dhekelia bases hit; European evacuations)</li>
        <li><b>Support/Defensive Roles:</b> United Kingdom (bases/intercepts in Cyprus/Bahrain/Qatar), France/Germany/Italy/Netherlands/Greece (defending Cyprus/Europe; naval/air), NATO (collective intercepts in Turkey airspace)</li>
    </ul>
    <p style="margin:10px 0 0 0; font-size:12px; color:#555;">
        Rapidly evolving; based on public reports (Al Jazeera, Britannica, Axios, CNN, ISW). Casualties rising; oil prices >$115/barrel; Strait of Hormuz disruptions.
    </p>
</div>
"""
