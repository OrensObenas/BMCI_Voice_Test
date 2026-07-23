import subprocess
import time
import sys
import os

def main():
    # S'assurer que le chemin absolu vers l'interpréteur python du venv est utilisé
    python_exe = sys.executable
    script_path = "agent.py"
    cmd = [python_exe, "-u", script_path, "dev"]
    
    print("=" * 60)
    print("Démarrage du boucle de résilience pour l'agent LiveKit...")
    print(f"Commande : {' '.join(cmd)}")
    print("Pour arrêter proprement, faites Ctrl+C.")
    print("=" * 60)
    
    while True:
        try:
            # Lancer le worker en tant que sous-processus avec redirection de flux pour capture dans les logs
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            # Lire et afficher les logs du sous-processus en temps réel
            for line in process.stdout:
                print(line, end='', flush=True)
            process.wait()
            
            # Vérifier le code de sortie
            if process.returncode == 0:
                print("\n[Runner] L'agent s'est arrêté proprement (Code 0). Fin de la boucle.")
                break
            else:
                print(f"\n[Runner] L'agent a crashé ou s'est déconnecté (Code de retour: {process.returncode}).")
                print("[Runner] Redémarrage automatique dans 2 secondes...")
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n[Runner] Interruption par l'utilisateur (Ctrl+C). Fermeture...")
            if 'process' in locals() and process.poll() is None:
                process.terminate()
            break
        except Exception as e:
            print(f"\n[Runner] Erreur inattendue dans le superviseur : {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
