import UnityPy
import os

BASE_DIR = os.path.dirname(__file__)
BASE_OUTPUT = os.path.join(BASE_DIR, "extracted")

def safe_write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if data is None:
        return False
    if isinstance(data, str):
        data = data.encode("utf-8")
    with open(path, "wb") as f:
        f.write(data)
    return True

def clean_name(name):
    return "".join([c for c in name if c.isalnum() or c in (' ', '_', '-')]).strip().replace(" ", "_")

def export_mesh(data, name):
    out_dir = f"{BASE_OUTPUT}/mesh"
    os.makedirs(out_dir, exist_ok=True)
    path = f"{out_dir}/{name}.obj"

    try:
        mesh_data = data.export()
        if not mesh_data:
            print(f"[SKIP] {name} (Vertex data is stripped or unreadable)")
            return

        with open(path, "w", encoding="utf-8") as f:
            f.write(mesh_data)
        print(f"[OK] mesh -> {path}")

    except Exception as e:
        print(f"[FAIL] mesh {name}: {e}")

def extract_obj(data, obj_type, name):
    name = clean_name(name)
    
    # List of supported types
    supported_types = ["Texture2D", "AudioClip", "TextAsset", "Mesh"]

    if obj_type not in supported_types:
        print(f"[!] {name} | {obj_type} is not supported. Only texture, mesh, text, audio extractor support.")
        return

    if obj_type == "Texture2D":
        try:
            out = f"{BASE_OUTPUT}/textures/{name}.png"
            os.makedirs(os.path.dirname(out), exist_ok=True)
            data.image.save(out)
            print(f"[OK] texture -> {out}")
        except:
            try:
                raw = f"{BASE_OUTPUT}/textures/{name}.tex"
                if safe_write(raw, data.image_data):
                    print(f"[RAW] texture -> {raw}")
            except:
                print(f"[FAIL] texture {name}")

    elif obj_type == "AudioClip":
        try:
            if not hasattr(data, 'samples') or not data.samples:
                print(f"[FAIL] audio {name} (no samples)")
                return
            for n, clip in data.samples.items():
                out = f"{BASE_OUTPUT}/audio/{clean_name(n)}.wav"
                safe_write(out, clip)
                print(f"[OK] audio -> {out}")
        except:
            print(f"[FAIL] audio {name}")

    elif obj_type == "TextAsset":
        try:
            out = f"{BASE_OUTPUT}/text/{name}.txt"
            content = getattr(data, "script", None) or getattr(data, "m_Script", None)
            if content is not None:
                if safe_write(out, content):
                    print(f"[OK] text -> {out}")
                else:
                    print(f"[FAIL] text {name} (empty content)")
            else:
                print(f"[FAIL] text {name} (no script attribute found)")
        except Exception as e:
            print(f"[FAIL] text {name}: {e}")

    elif obj_type == "Mesh":
        export_mesh(data, name)

def pick_file():
    files = [f for f in os.listdir(BASE_DIR) if os.path.isfile(os.path.join(BASE_DIR, f))]
    print("\nFILES\n")
    for i, f in enumerate(files):
        print(f"[{i}] {f}")

    idx = input("\nfile id: ").strip()
    if not idx.isdigit(): return None
    idx = int(idx)
    if idx < 0 or idx >= len(files): return None
    return os.path.join(BASE_DIR, files[idx])

def main():
    path = pick_file()
    if not path: return

    try:
        env = UnityPy.load(path)
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    types = {}

    for obj in env.objects:
        try:
            data = obj.read()
        except:
            continue

        t = obj.type.name
        name = getattr(data, "m_Name", None) or getattr(data, "name", None)
        if not name:
            name = f"{t}_{obj.path_id}"

        info = f"{name} | {t} | id:{obj.path_id}"
        if t not in types:
            types[t] = []
        types[t].append((data, t, name, info, obj.path_id))

    type_list = sorted(list(types.keys()))
    print("\nTYPES\n")
    for i, t in enumerate(type_list):
        print(f"[{i}] {t} ({len(types[t])})")

    tid = input("\ntype id: ").strip()
    if not tid.isdigit(): return
    tid = int(tid)
    if tid < 0 or tid >= len(type_list): return

    selected_type = type_list[tid]
    all_items = types[selected_type]
    filtered = all_items

    def show(items):
        print(f"\nASSETS ({selected_type})\n")
        for i, (_, _, _, info, _) in enumerate(items):
            print(f"[{i}] {info}")

    show(filtered)

    while True:
        print("\n[1] extract one")
        print("[2] extract all")
        print("[/search text] filter")
        print("[0] exit")
        mode = input("> ").strip()

        if mode == "0":
            break
        elif mode.startswith("/search"):
            keyword = mode.replace("/search", "").strip().lower()
            filtered = [x for x in all_items if keyword in x[2].lower()]
            show(filtered)
        elif mode == "1":
            user_input = input("id: ").strip()
            if not user_input.isdigit(): continue
            val = int(user_input)
            selected = None
            if 0 <= val < len(filtered):
                selected = filtered[val]
            else:
                for item in filtered:
                    if str(item[4]) == str(val):
                        selected = item
                        break
            if not selected:
                print("not found")
                continue
            extract_obj(selected[0], selected[1], selected[2])
        elif mode == "2":
            for item in filtered:
                extract_obj(item[0], item[1], item[2])

if __name__ == "__main__":
    main()
