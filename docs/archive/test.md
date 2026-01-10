let's read @docs and the complete code base.

I'd like to create a team of ai agents with crewai.
The aim is to be able to obtain in French at runtime

A weekly menu adapted
-- to my constraints (family, children, medical condition, .... )
-- to the season from today's date
-- with starter, main course and dessert only at lunchtime on weekends
-- for lunch and dinner only (not mornings)
with recipes for each menu item
-- in html format
-- in paprika3 format (via an existing tool)
and an aggregated list of ingredients for the week's shopping

I think it's a good idea to create a team of agents with crewai like this : 

1. Agent: "Menu Planner"
Role: Develops the menu for the week, taking into account all constraints and seasonal specificities.
Objective: Produce a structured menu plan for lunch and dinner, with starters, main courses and desserts for weekend lunches only.
Possible tools:
A tool to retrieve the current date and determine the season.
A tool to interpret constraints provided by the user (family, children, medical conditions, etc.).
2. Agent: "Recipe Detailer"
Role: Generates detailed recipes for each dish on the menu.
Objective: Provide recipes in HTML and Paprika3 format.
Possible tools:
A recipe generation tool capable of producing HTML.
An existing Paprika3 tool (as you mentioned) to export recipes in this specific format.
3. Agent: "Ingredients Manager"
Role: Collects and aggregates all the ingredients needed for the week's menu.
Objective: To create a consolidated and organised shopping list.
Possible tools:
A tool to extract the ingredients for each recipe.
A tool for grouping similar ingredients and calculating total quantities.
Tasks and Workflow
Here's how the agents might interact to accomplish the task:

Initial Task (Menu Planner): The Menu Planner receives your constraints and the current date. It generates a structured menu proposal (lunch/evening, weekend specials) in French, adapted to the season.
Detail Task (Recipe Detailer): Once the menu has been validated, the Recipe Detailer takes each dish on the menu and generates the corresponding recipe in HTML using the Paprika3 tool.
Aggregation Task (Ingredient Manager): Simultaneously with or after recipe generation, the Ingredient Manager collects information from the recipes to create the aggregated shopping list.
Key Implementation Considerations
Constraint Management: The way in which you “inject” your constraints (allergies, food preferences, number of people, desired preparation time, etc.) will be crucial. You can pass them on as arguments to your Menu Planner agent.
Paprika3 tool integration: Make sure that your "existing Paprika3 tool" can be easily called and interacts with your Python code in CrewAI. This could be a Python function that takes the recipe details and converts them to Paprika3 format.
French output: All agent interactions and output will need to be set to generate French content.

Validation and Iteration: At the start, you'll probably have to iterate on your agents' “prompts” and task orchestration to get the desired results.

I think we can use CookingCrew for some of the request but I let you decide.
If we use cooking crew, we should not break it.

- I want to inject the crew(s) in the global @main.py flow with action being MENU

they agents should  look at @tools_handbook.md to find the best tools and tell if something is missing

The resulting report menu  should :

- be created using @ReportingTool
- be send by mail using @PostCrew as usual
- in french

The list of items, the receipes and the aggregated list of ingredients should not be in the report, only on disks

@FinDailyCrew is a good example of well architectured crew

Remember :

- @agents.yaml should be brief on the tools they can use
- async_execution: true is welcome
- be sure to follow the flow for adding this crews, it has many impact, review @DESIGN_PRINCIPLES.md and @content_state.py and @main.py

use @MenuDesignerCrew  to host the concept
