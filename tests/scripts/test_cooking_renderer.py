#!/usr/bin/env python3
"""
Test script to generate a sample cooking HTML with the improved renderer
"""

import sys
from pathlib import Path

from epic_news.utils.html.template_manager import TemplateManager

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


# Sample recipe data
sample_recipe = {
    "recipe_title": "Salade César Gourmet",
    "name": "Salade César Gourmet",
    "description": "Une version raffinée de la célèbre salade César avec des croûtons maison et une sauce crémeuse authentique",
    "type": "Entrée",
    "category": "Salade",
    "prep_time": "20 minutes",
    "cook_time": "10 minutes",
    "total_time": "30 minutes",
    "servings": "4 personnes",
    "difficulty": "Facile",
    "ingredients": [
        "2 cœurs de laitue romaine",
        "100g de parmesan râpé",
        "4 tranches de pain de campagne",
        "2 gousses d'ail",
        "4 filets d'anchois",
        "2 jaunes d'œufs",
        "1 citron (jus)",
        "100ml d'huile d'olive",
        "1 cuillère à café de moutarde de Dijon",
        "Poivre noir fraîchement moulu",
    ],
    "instructions": [
        "Préchauffez le four à 200°C. Coupez le pain en cubes et faites-les dorer au four pendant 8-10 minutes pour obtenir des croûtons croustillants.",
        "Lavez et essorez soigneusement la laitue romaine. Coupez-la en morceaux de taille moyenne.",
        "Préparez la sauce : dans un bol, écrasez l'ail et les anchois. Ajoutez les jaunes d'œufs et la moutarde.",
        "Incorporez progressivement l'huile d'olive en fouettant pour émulsionner la sauce.",
        "Ajoutez le jus de citron et assaisonnez avec le poivre noir.",
        "Dans un grand saladier, mélangez la laitue avec la sauce César.",
        "Ajoutez les croûtons et la moitié du parmesan. Mélangez délicatement.",
        "Servez immédiatement avec le reste du parmesan râpé sur le dessus.",
    ],
    "chef_notes": [
        "Pour une sauce plus authentique, utilisez des anchois de qualité et écrasez-les bien.",
        "Les croûtons peuvent être préparés à l'avance et conservés dans une boîte hermétique.",
        "Ajoutez la sauce juste avant de servir pour éviter que la salade ne se ramollisse.",
    ],
    "nutritional_info": {
        "calories": "320 kcal par portion",
        "proteins": "12g",
        "carbs": "18g",
        "fats": "24g",
        "fiber": "3g",
    },
}


def main():
    """Generate sample cooking HTML"""
    print("🍳 Testing improved cooking renderer...")

    # Create template manager
    template_manager = TemplateManager()

    # Generate HTML using the universal template
    html_content = template_manager.render_report("COOKING", sample_recipe)

    # Save to file
    output_file = Path(__file__).parent / "test_cooking_output.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Generated test cooking HTML: {output_file}")
    print("🌐 Open the file in your browser to see the improved styling!")


if __name__ == "__main__":
    main()
