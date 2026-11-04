import os
import glob
import subprocess
from pathlib import Path

REPLAY_DIR = r"C:\Users\kazam\Documents\My Games\Rocket League\TAGame\DemosEpic"
PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "parsed" / "rocketrp_test"

def get_latest_replay(replay_dir):
    search_path = os.path.join(replay_dir, "*.replay")
    list_of_files = glob.glob(search_path)
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getmtime)

def main():
    print("🔎 Ricerca dell'ultimo replay di Rocket League...")
    latest_replay_path = get_latest_replay(REPLAY_DIR)
    
    if not latest_replay_path:
        print(f"❌ Nessun file .replay trovato.")
        return

    print(f"✅ Trovato ultimo replay: {os.path.basename(latest_replay_path)}")
    
    # Assicuriamoci che la cartella di output esista
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    rocketrp_path = r"C:\Users\kazam\Downloads\RocketRP.CLI.1.2.19\RocketRP.CLI.exe"
    
    # Usiamo i flag espliciti -r e -o come da help ufficiale
    cmd = [
        rocketrp_path, 
        "parse", 
        "-r", latest_replay_path, 
        "-o", str(OUTPUT_DIR),
        "-p"  # Abilitiamo anche il pretty-print per leggibilità
    ]
    
    print(f"⚡ Avvio della conversione con RocketRP verso la cartella: {OUTPUT_DIR}")
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("🎉 Conversione completata con successo!")
        
        # Stampiamo i file presenti nella cartella di output per conferma immediata
        generated_files = list(OUTPUT_DIR.glob("*.json"))
        print("\n📁 File JSON attualmente presenti in output:")
        for f in generated_files:
            print(f" - {f.name} (Modificato: {os.path.getmtime(f)})")
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Errore durante l'esecuzione di RocketRP:\n{e.stderr}")

if __name__ == "__main__":
    main()