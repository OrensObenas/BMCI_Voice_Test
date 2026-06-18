"""
Dialogue bancaire de test pour le benchmark TTS.
21 répliques alternant agent et client, couvrant :
- Politesse / formalité
- Émotion (colère, frustration, satisfaction)
- Chiffres et montants
- Vocabulaire bancaire spécialisé
- Accents et intonations variées
"""

from dataclasses import dataclass


@dataclass
class DialogueLine:
    """Une réplique du dialogue."""
    id: int
    role: str          # "agent" ou "client"
    text: str
    emotion: str       # Émotion dominante
    difficulty: str    # "easy", "medium", "hard" (pour le TTS)


DIALOGUE: list[DialogueLine] = [
    DialogueLine(
        id=1, role="agent",
        text="Bonjour, bienvenue chez Atlas Bank. Comment puis-je vous aider ?",
        emotion="neutre",
        difficulty="easy",
    ),
    DialogueLine(
        id=2, role="client",
        text="Bonjour. Je suis venu pour retirer cent mille dirhams de mon compte, maintenant.",
        emotion="déterminé",
        difficulty="medium",  # Chiffres
    ),
    DialogueLine(
        id=3, role="agent",
        text="Bien sûr monsieur, est-ce que vous avez votre carte et votre CIN avec vous ?",
        emotion="professionnel",
        difficulty="easy",
    ),
    DialogueLine(
        id=4, role="client",
        text="Oui, les voilà. Et je vais retirer mes cent mille dirhams aujourd'hui, vous m'avez bien compris ?",
        emotion="insistant",
        difficulty="medium",
    ),
    DialogueLine(
        id=5, role="agent",
        text="Merci monsieur. Je vous comprends bien. Mais il y a un problème, ce montant est très élevé.",
        emotion="prudent",
        difficulty="easy",
    ),
    DialogueLine(
        id=6, role="client",
        text="Hein ? Quel problème ? C'est mon argent, pas le vôtre !",
        emotion="irrité",
        difficulty="hard",  # Exclamation + émotion
    ),
    DialogueLine(
        id=7, role="agent",
        text=(
            "Oui monsieur, vous avez tout à fait raison, c'est votre argent. "
            "Mais la banque a son règlement : il est impossible de retirer plus de "
            "cinquante mille dirhams par jour sans rendez-vous préalable."
        ),
        emotion="explicatif",
        difficulty="hard",  # Long + chiffres
    ),
    DialogueLine(
        id=8, role="client",
        text=(
            "Non, non, non ! C'est inacceptable ! Je me suis déplacé de loin "
            "et maintenant vous me dites que c'est impossible ?! Honte à vous !"
        ),
        emotion="colère",
        difficulty="hard",  # Très émotionnel
    ),
    DialogueLine(
        id=9, role="agent",
        text=(
            "Je suis vraiment désolé monsieur, mais ce règlement n'est pas de moi, "
            "c'est la réglementation de Bank Al-Maghrib. Cette procédure existe pour "
            "vous protéger, vous et la banque."
        ),
        emotion="empathique",
        difficulty="hard",  # Noms propres + long
    ),
    DialogueLine(
        id=10, role="client",
        text=(
            "Je ne veux pas d'excuses ! Je veux mon argent maintenant ! "
            "Si vous ne me le donnez pas, je vais voir le directeur !"
        ),
        emotion="furieux",
        difficulty="hard",
    ),
    DialogueLine(
        id=11, role="agent",
        text=(
            "Bien sûr monsieur, je peux vous conduire vers le directeur. "
            "Mais donnez-moi une minute — il y a une autre solution : "
            "on peut fixer un rendez-vous pour demain pour retirer le montant total, "
            "ou je peux vous faire un virement bancaire vers un autre compte si vous le souhaitez."
        ),
        emotion="solution",
        difficulty="hard",  # Très long
    ),
    DialogueLine(
        id=12, role="client",
        text=(
            "Un rendez-vous pour demain ? Mais j'ai besoin de l'argent maintenant ! "
            "C'est quoi votre problème ?"
        ),
        emotion="exaspéré",
        difficulty="medium",
    ),
    DialogueLine(
        id=13, role="agent",
        text=(
            "Je comprends votre frustration monsieur. Pouvez-vous me dire pourquoi "
            "vous avez besoin de ce montant maintenant ? Peut-être que nous pouvons "
            "trouver une solution adaptée ensemble."
        ),
        emotion="empathique",
        difficulty="medium",
    ),
    DialogueLine(
        id=14, role="client",
        text=(
            "Je veux acheter une maison. Le vendeur a besoin de l'argent aujourd'hui, "
            "sinon il va la vendre à quelqu'un d'autre."
        ),
        emotion="urgent",
        difficulty="medium",
    ),
    DialogueLine(
        id=15, role="agent",
        text=(
            "Ah, je comprends monsieur. Dans ce cas, le virement bancaire est la meilleure "
            "et la plus sûre des solutions. On peut le faire immédiatement, le vendeur recevra "
            "ses cent mille dirhams dans la journée même. Et en plus, vous n'avez pas à porter "
            "du liquide sur vous."
        ),
        emotion="rassurant",
        difficulty="hard",  # Très long + chiffres
    ),
    DialogueLine(
        id=16, role="client",
        text="Un virement ? Mais est-ce qu'il va vraiment le recevoir aujourd'hui ?",
        emotion="sceptique",
        difficulty="easy",
    ),
    DialogueLine(
        id=17, role="agent",
        text=(
            "Oui monsieur, si on le fait avant midi, il arrivera le même jour. "
            "Et cette procédure est bien plus sûre, sans aucun risque de vol d'espèces."
        ),
        emotion="confiant",
        difficulty="medium",
    ),
    DialogueLine(
        id=18, role="client",
        text=(
            "D'accord... c'est raisonnable. Mais la prochaine fois, j'ai besoin de connaître "
            "ces règles à l'avance. Je me suis déplacé sans être au courant."
        ),
        emotion="résigné",
        difficulty="medium",
    ),
    DialogueLine(
        id=19, role="agent",
        text=(
            "Vous avez entièrement raison monsieur, et je m'excuse sincèrement pour ce désagrément. "
            "Je vais vous remettre une brochure avec toutes les informations utiles. "
            "Alors, on procède à votre virement ?"
        ),
        emotion="aimable",
        difficulty="medium",
    ),
    DialogueLine(
        id=20, role="client",
        text="Oui, allons-y. Merci pour votre patience.",
        emotion="satisfait",
        difficulty="easy",
    ),
    DialogueLine(
        id=21, role="agent",
        text=(
            "Merci à vous monsieur pour votre compréhension. "
            "Vous êtes toujours le bienvenu chez Atlas Bank."
        ),
        emotion="chaleureux",
        difficulty="easy",
    ),
]


def get_all_texts() -> list[str]:
    """Retourne tous les textes du dialogue."""
    return [line.text for line in DIALOGUE]


def get_texts_by_role(role: str) -> list[DialogueLine]:
    """Retourne les répliques d'un rôle donné."""
    return [line for line in DIALOGUE if line.role == role]


def get_texts_by_difficulty(difficulty: str) -> list[DialogueLine]:
    """Retourne les répliques d'une difficulté donnée."""
    return [line for line in DIALOGUE if line.difficulty == difficulty]


def get_total_chars() -> int:
    """Nombre total de caractères dans le dialogue."""
    return sum(len(line.text) for line in DIALOGUE)


if __name__ == "__main__":
    print(f"Dialogue : {len(DIALOGUE)} répliques")
    print(f"Total caractères : {get_total_chars()}")
    print(f"  Easy: {len(get_texts_by_difficulty('easy'))}")
    print(f"  Medium: {len(get_texts_by_difficulty('medium'))}")
    print(f"  Hard: {len(get_texts_by_difficulty('hard'))}")
    print(f"  Agent: {len(get_texts_by_role('agent'))}")
    print(f"  Client: {len(get_texts_by_role('client'))}")
