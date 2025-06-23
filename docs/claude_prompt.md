# To easily create a new feature

## Create a crew

let's read @docs and the complete code base.

- I want to inject @SaintDailyCrew in the global @main.py flow with action being SAINT

this crew should

- search on internet the saint of day in switzerland for today
- you can use wikipedia tools and other tools
- look at @tools_handbook.md to find the best

The resulting report should :

- be created using @ReportingTool
- be send by mail using @PostCrew as usual
- in french

@FinDailyCrew is a good example of well architectured crew

Remember :

- @agents.yaml should be brief on the tools they can use
- async_execution: true is welcome
- be sure to follow the flow for adding this crews, it has many impact, review @DESIGN_PRINCIPLES.md and @content_state.py and @main.py

## Create a tool

- read our @DESIGN_PRINCIPLES.md, use @accuweather_tool.py as a template
- create a wikipedia tool to permit agent to use this knowledge
- create a test for this tool
- update documentation while ensure that we stay in proper alphabetical order for the list of tools
- add a main to tool to show how to use the tool

## Create a team

J'aimerais creer une equipe d'ai agents avec crewai.

Le but est de pouvoir obtenir  en francais à l'execution

- un menu de la semaine adapté

-- à mes contraintes (famille, enfant, condition medicale, .... )

-- à la saison à partir de la date du jour

-- avec entree, plat et dessert uniquement le midi des weekend

-- pour le midi et le soir uniquement (pas le matin)

- les recettes pour chaque élément du menu

-- au format html

-- au format paprika3 (via un tools existant)

- la liste agrégée des ingrédients pour faire les courses pour la semaine
