# 4. Epic News User Guide

This guide shows you exactly what you can ask Epic News to do. Simply use natural language—no special commands needed.

## 1. How to Use Epic News

1.  **Start the application**: Run `crewai flow kickoff` in your terminal.
2.  **Make a request**: When prompted, type your request in natural language.
3.  **Automatic Handling**: Epic News automatically classifies your request and assigns the appropriate crew to handle the task.
4.  **Receive Report**: You will receive a detailed report via email and locally in the `output/` directory.

## 2. Supported Use Cases & Example Prompts

### 📈 Finance (FinDailyCrew)
**What it does:** Analyzes your stock/crypto portfolio (from `data/stock.csv` and Kraken API) and provides BUY/SELL/KEEP recommendations.
- "Analyze my portfolio and suggest trades."
- "Give me today's financial analysis."
- "What should I buy or sell today?"

### 📰 News & Research (NewsCrew)
**What it does:** Generates comprehensive news reports on any topic with analysis and insights.
- "Latest news about artificial intelligence."
- "What's happening with Tesla stock?"
- "News summary about renewable energy."

### 📡 RSS Weekly (RssWeeklyCrew)
**What it does:** Generates weekly summaries from your RSS feeds defined in `data/feedly.opml`.
- "Generate my weekly RSS summary."
- "What happened this week in my feeds?"
- "Weekly tech news roundup."

### 🍳 Cooking (CookingCrew)
**What it does:** Creates detailed recipes with ingredients, steps, and an export link for the Paprika app.
- "Recipe for chocolate chip cookies."
- "How to make beef bourguignon?"
- "Vegetarian pasta recipe for 4 people."

### 🛒 Shopping Advisor (ShoppingAdvisorCrew)
**What it does:** Provides comprehensive product research, price comparisons for Switzerland/France, competitor analysis, and shopping recommendations.
- "I need shopping advice for a MacBook Pro M4."
- "Compare prices for an iPhone 15 Pro in Switzerland and France."
- "Best laptop under 1500 CHF with pros and cons."

### 📚 Book Summary (LibraryCrew)
**What it does:** Generates comprehensive book summaries with key insights and takeaways.
- "Summarize 'The Lean Startup'."
- "Book summary of 'Atomic Habits'."
- "What are the main points of '1984'?"

### 🤝 Meeting Prep (MeetingPrepCrew)
**What it does:** Prepares you for meetings with company research, profiles, and strategic talking points.
- "Prepare me for a meeting with Microsoft."
- "Meeting preparation for Apple Inc."
- "Research Google before our call."

### 🕵️ OSINT Intelligence
**What it does:** Conducts deep company intelligence gathering, including profiles, tech stacks, web presence, and HR analysis.
- "Full intelligence report on OpenAI."
- "Research everything about Stripe."
- "Complete OSINT analysis of Airbnb."

### ✈️ Travel Planning (HolidayPlannerCrew)
**What it does:** Creates detailed travel itineraries with activities, restaurants, and local insights.
- "Plan a 5-day trip to Tokyo."
- "Holiday itinerary for Paris in spring."
- "Weekend getaway to Barcelona."

### ⛪ Saint of the Day (SaintDailyCrew)
**What it does:** Gets the saint of the day for Switzerland.
- "Who is the saint of the day?"
- "Saint of the day."

### ���� Creative Writing (PoemCrew)
**What it does:** Generates creative poems on any topic.
- "Write a poem about artificial intelligence."
- "Poem about the ocean at sunset."

## 3. Advanced Features
- **Multi-source Research:** Combines web scraping, APIs, and databases for comprehensive analysis.
- **Professional Reports:** All outputs are delivered as professional HTML reports.
- **Email Integration:** Results are automatically delivered via email.
- **Intelligent Caching:** Caching is used to speed up requests and avoid API rate limits.
