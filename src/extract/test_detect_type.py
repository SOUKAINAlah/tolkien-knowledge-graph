from src.extract.detect_type import detect_infobox_name

for title in ["Rivendell", "Aman", "White Council", "Elrond"]:
    print(title, "->", detect_infobox_name(title))
