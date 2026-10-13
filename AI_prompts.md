# AI Prompts Log — Homework 5a

A log of every prompt given to the AI assistant, grouped by part. For each prompt after the first in a part, a short note captures what the first prompt was missing.

---

## Part 1: Project Setup, Shop Database, and Prompt Log

### Prompt 1

> we are working in homework 5a

### Prompt 2

> ok, I'm just telling you this information for background so you know where we are going with it. Do nothing with it.
>
> So today we are going to build multi-agent operations that will run the campus customs shop. open tickets land on a board and they take care of whatever is needed to run the shop. We will be building three pieces, an MCP server, fast api backend with multi agent team, and react dashboard so we can watch the agents. agents will ahev full connectivity and we will be building a bunch of agents, including a boss, that reads tickets, delegates, and makes funal calls, inventory that checks inventory inof and which and when need restock, accoutning that watches key accounting info and prepares payments, facilities that handles shop space and overhead, customer service that drafts messages to customers.
>
> I will be sharing a database which is the OG shop database. We will eventually make a copy of the database and call it campus_customs_new.db. We want to keep the OG database the same.
>
> A few rules: the desk.date_today is "today" for the shop and can be used to determine what is overdue. Vendor leadtimes should come from the vendor table. vendors will not ship inventory whenever they have an open unpaid invoice, human approval is required for payments, points will be deduced if this doesnt work. If there is not enough money, the pay tool must reject as there can be no negative balances, cash only goes out in this homework. before a full run to resolve a ticket, make sure reset the copy database to original value. And do not actually email customers, only draft drafts.
>
> Make sure use portkey_api_key and ONLY use gpt-6-luna. if you use anything else, I will lose points and waste a bunch of money.

**Missing from the first prompt:** It named the folder but left out the assignment (a multi-agent team running the Campus Customs shop from a ticket board), the three pieces (MCP server, FastAPI backend, React dashboard), the five agents, the shop rules, and the required model (`gpt-6-luna` through Portkey).

### Prompt 3

> @"/Users/paulwillems/Downloads/data/"
> heres data

**Missing from the first prompt:** It didn't provide the shop data, so this points to the original `campus_customs.db` the agents will work from.

### Prompt 4

> goa head and copy it

**Missing from the first prompt:** It didn't ask for a working copy, so this creates `data/campus_customs_new.db` and leaves the original database untouched.

### Prompt 5

> ok create an AI_prompts.md file with the same set up as homework 4

**Missing from the first prompt:** It didn't ask for any record of the work, so this adds a prompt log formatted like the one from homework 4.

### Prompt 6

> can we turn this into a skill called ai_prompt_setup

**Missing from the first prompt:** It didn't ask to reuse the setup, so this packages the prompt-log format into a reusable `ai-prompt-setup` skill for future homeworks.

---

## Part 2: Understanding the Shop Database

### Prompt 1

> moving onto part 3

### Prompt 2

> part 2

**Missing from the first prompt:** It gave the wrong part number, so this corrects it to Part 2.

### Prompt 3

> we are going to be looking at the database, don't do anything yet with that

**Missing from the first prompt:** It didn't say what the part was about, so this sets the topic (studying the shop database) and says to wait for instructions.

### Prompt 4

> ok take a look at the campus_customs database. make sure to look through every field and table. once you've done that create a copy called campus_customs_new. we will use the copy as the working copy and updating it moving forward. take a moment to also examine the open tickets. create an output folder and put a harness.md file in there. In the harness file for each table list all the fields and a short specific line about why that table would matter to the agent. the file will continue to be added to throughout

**Missing from the first prompt:** It didn't give a task, so this asks for a full review of every table and field, a working copy (`campus_customs_new.db`), a look at the open tickets, and an `output/harness.md` listing each table's fields and why it matters to the agents.

---

## Part 3: Building the MCP Server

### Prompt 1

> ok moving onto problem 3

### Prompt 2

> we are going to be building an mcp server, do nothing with that

**Missing from the first prompt:** It didn't say what the part was about, so this sets the topic (building the MCP server) and says to wait for instructions.

### Prompt 3

> ok, we are going to be building it in mcp_server/ using fastmcp which will talk to campus_customs_new.db. No need to run or connect it for this part, I will tell you when to do that.

**Missing from the first prompt:** It didn't say where or how to build it, so this sets the folder (`mcp_server/`), the library (FastMCP), the database it uses (`campus_customs_new.db`), and says not to run or connect it yet.

### Prompt 4

> Every agent for this problem will be using this MCP server. write three tools you know you will need based on the tickets in the database. Name those tools clearly and succinctly. Never invent any data, only use what is in the database. Once you have made those three tools, add into the harness file the tools, which table the tool reads, which ticket it is unlocking, and one specific sentence about why that tool is important and the right one for unlocking that ticket. In the sentences, vague descriptions will be graded poorly, so make sure to tie the tool to the ticket clearly.

**Missing from the first prompt:** It didn't say what tools to build, so this asks for exactly three clearly named tools tied to the open tickets, using only database values, plus a harness entry for each with the tables it reads, the ticket it unlocks, and a specific reason it fits that ticket.

### Prompt 5

> also add a README.md file in the mcp_server file that explains what the server is for, which data file it uses, and the three tools it has

**Missing from the first prompt:** It didn't ask for documentation, so this adds `mcp_server/README.md` explaining the server's purpose, the data file it uses, and its three tools.

---

## Part 4: Connecting and Testing the MCP Server

### Prompt 1

> moving onto part 4

### Prompt 2

> ok we are going to be adding the mcp server to the vibe coder and then test each of the tools, do nothing with that just yet.

**Missing from the first prompt:** It didn't say what the part was about, so this sets the topic (connecting the MCP server to the coding assistant and testing each tool) and says to wait for instructions.

### Prompt 3

> ok, I want to add the mcp server we just made to this project so we can call up the tools. Save that connection in .mcp.json file at the project root or however you normally save local mcp server lists. once connected, test each of the three mcp tools and save the evidence that it works in output/mcp_smoke.json. For every tool include the prompt you asked to test it, the tool name, and the tool output. make sure it matches values that are in the database.

**Missing from the first prompt:** It didn't say how to connect or what to deliver, so this saves the server in `.mcp.json`, asks for a test of all three tools, and requires `output/mcp_smoke.json` with each test prompt, tool name, and output checked against the database.

---

## Part 5: Building the Agent Team and Expanding the MCP Tools

### Prompt 1

> moving onto part 5

### Prompt 2

> ok we are going to be building an agent team and expanding the mcp tools available. don't do anything with that

**Missing from the first prompt:** It didn't say what the part was about, so this sets the topic (building the agent team and adding more MCP tools) and says to wait for instructions.

### Prompt 3

> ok, we are building the agent team for campus customs using pydanticAI. make a boss, inventory, accounting, facilliaties, and customer services. Include prompts, models, and agent loops so they can delegate work to each other. put agents prompts in backend/prompts making one file for each agent.  put data types in backend/models.py, and the agent files in the backend file. Make sure each of the roles is very clear. Use the portkey_api_key and only use luna-6-gpt. if you use soemthing else, I will lose points. For the prompts, write them with the shop rules that the agent needs. the more detailed the prompt the better. Before you write each prompt, show it to me and I will offer clear edits.

**Missing from the first prompt:** It didn't give the build details, so this specifies PydanticAI, the five agents with clear roles, delegation loops between them, where prompts (`backend/prompts/`, one file per agent), data types (`backend/models.py`) and agent code (`backend/`) go, the Portkey key and required model, and asks to review each prompt before it is written.

### Prompt 4

> This looks good, just know that more generic vague answers will lead to lower scores.

**Missing from the first prompt:** It didn't set a quality bar for agent answers, so this approves the Boss prompt and warns that generic, vague answers will score lower.

### Prompt 5

> looks good, and yes, the model is gpt-6-luna

**Missing from the first prompt:** It gave the model as `luna-6-gpt`, so this confirms the exact model ID is `gpt-6-luna` and approves the Inventory prompt.

### Prompt 6

> know that vague generic prompts will lead to lower scores. If you feel like you shoudl edit any of the other two to be more specific to this project, go ahead.

**Missing from the first prompt:** It didn't say the prompts themselves had to be project-specific, so this approves the Accounting prompt and allows edits to the Boss and Inventory prompts to tie them more closely to Campus Customs.

### Prompt 7

> looks good

**Missing from the first prompt:** It didn't review any prompt, so this approves the Facilities prompt.

### Prompt 8

> looks good

**Missing from the first prompt:** It didn't review any prompt, so this approves the Customer Service prompt, the last of the five.

### Prompt 9

> ok I saw that you added tools, but if there are any additional tools you want to add, add those. make sure the shop facts come from the database and that nothing is made up and do not invent a second shop-tool layer that bypasses the mcp. Wire the agents so that as they run they append information to outputs/audit_trail.json. for each agent loop step record key information that would allow for an audit later. do not wipe this document after each run, add to it. In the harness file, list each of the agents and each of the mcp tools along with which table the tool is using. Add a short safety section that includes vital guardrails a business like campus customs would want to if agents interact with real customers and real money. also include token limits to keep token use in check. also update the mcp README.md file with all the tools that built.

**Missing from the first prompt:** It didn't cover data integrity, auditing, safety or cost, so this requires every shop fact to come through the MCP server with no bypass layer, an append-only `output/audit_trail.json` recording every agent loop step, a harness listing every agent and MCP tool with its tables, a safety section, token limits, and a full tool list in the MCP README.

---

## Part 6: Planning the Three Tickets

### Prompt 1

> moving onto part 6

### Prompt 2

> ok we are going to be planning the three tickets

**Missing from the first prompt:** It didn't say what the part was about, so this sets the topic (planning how the team handles the three open tickets).

### Prompt 3

> ok, build an desk_tickets.html, which is a page you can double click into with one tab per ticket. also add empty cash and reflections tabs for later problems and just write "under construction" with a sad face emoji wearing a construction hat. in each ticket tab, add in an expected section and actual section. In the expected section, it will include the who will the boss call on first and why, all the agent delegations you expect be specific do not write that the boss calls on everyone, and then with mcp tools you think will be run.

**Missing from the first prompt:** It didn't say what the plan should look like, so this asks for a double-clickable `desk_tickets.html` with a tab per ticket plus placeholder Cash and Reflections tabs, and Expected/Actual sections listing who the Boss calls first and why, the specific delegations, and the MCP tools expected to run.

### Prompt 4

> put the html into the output

**Missing from the first prompt:** It didn't say where to save the page, so this places `desk_tickets.html` in the output folder.

### Prompt 5

> update the name to output not outputs

**Missing from the first prompt:** It didn't name the folder exactly, so this asks for the folder to be called `output` instead of `outputs`.

### Prompt 6

> update the file name from outputs to output

**Missing from the first prompt:** It repeats the rename request, making clear the folder itself should be renamed from `outputs` to `output`.

---

## Part 7: Building the FastAPI Backend

### Prompt 1

> ok mmoving onto part 7

### Prompt 2

> ok we are going to be building the backend for the frontend. this backend will use fastapi. do not do anything with that just yet.

**Missing from the first prompt:** It didn't say what the part was about, so this sets the topic (a FastAPI backend to serve the frontend) and says to wait for instructions.

### Prompt 3

> this will be the backend for the frontend dashboard we will be pulling together in the next part. do not do anything with that just more for you to know

**Missing from the first prompt:** It didn't say what the backend would serve, so this explains it will power the React dashboard built in the next part.

### Prompt 4

> ok, for the abckend, which should be in backend/main.py , like i said it will be fastapi and will create routes that each accomplish this: return the three tickets and says whether open or resolved, take a ticket id and run agent team on that ticket, return recent agent events so that when the board refreshes it shows what each agent said and what tools it used, approve payment after a human click approves (agents only prepare the pay, its this route that actually changes the cash), return current checking balance from cash_accounts, reset database to original values when want to try a fresh run.  Once you have done that, from the backend folder, start the server with uvicorn main:app --reload --port 8000, so that the frontend can call it later.

**Missing from the first prompt:** It didn't define the API, so this puts it in `backend/main.py` with routes to list tickets as open or resolved, run the team on a ticket, return recent agent events, approve and execute a payment after a human click, return the checking balance, and reset the database, then start it with `uvicorn main:app --reload --port 8000`.

### Prompt 5

> in Harness.md, outline each route in one line. include what is the URL and what it does.

**Missing from the first prompt:** It didn't ask for the routes to be documented, so this adds a one-line entry for each route in `output/harness.md` with its URL and what it does.

### Prompt 6

> why are you still running the task fastapi?

**Missing from the first prompt:** It didn't say how long the server should keep running, so this asks why the FastAPI server is still running in the background.

---

## Part 8: Building the SpongeBob Dashboard

### Prompt 1

> ok, we are moving onto part 8

### Prompt 2

> ok we are going to build the frontend in /frontend and using vite+react+typescript. the page should call on the routes that were built in the backend. The dashboard needs to list all three tickets, let it pick one ticket and start the agent team, show each agent and what they are saying while doing tickets, mark a ticket resolved when the run is finished, show a short summary of what each agent did on that ticket, let a human approve a payment or purchase when asked, and show the checking balance which changes when payments or purchases are made. I want this dashboard to be impressive with how it looks. I want it to be in the spongebob theme where the boss is mr crabs, and the other agents are spongebob, squidward, patrick the star, sandy the squirrel. I also want planketon to run across the screen creating a trail of bubbles whenever a payment is approved and then when a purchase is made, I want gary the snail to slide across leaving a trail of slime. I am getting graded on how it looks and the usability so blow me away. The frontend should talk to the backend at the port 8000. on the backend allow the vite page origin so the browser is allowed to call routes. Start the board using npm run dev. In the output file add design.md with what chose for dashboard look, including layout, how agents read differently, how resolved tickets and cash show up) and why, including why the choices make the dashboard feel more special and user friendly.

**Missing from the first prompt:** It didn't describe the dashboard, so this specifies a Vite + React + TypeScript app in `frontend/` that lists and runs tickets, shows each agent live, marks tickets resolved, summarizes each agent's work, lets a human approve payments and purchases, and shows the changing balance, all in a SpongeBob theme with Plankton and Gary animations, wired to the backend on port 8000 with CORS, started with `npm run dev`, and explained in `output/design.md`.

---

## Part 9: Running and Resolving the Tickets

### Prompt 1

> moving onto part 9

### Prompt 2

> does it cost anything to keep those running?

**Missing from the first prompt:** It didn't ask about cost, so this asks whether leaving the backend and dashboard servers running costs anything.

### Prompt 3

> ok we are going to be running and resolving the tickets, do nothing with that yet

**Missing from the first prompt:** It didn't say what the part was about, so this sets the topic (running the agent team to resolve the tickets) and says to wait for instructions.

### Prompt 4

> ok before we do anything and runt he tickets, reset the database to make sure running from a blank slate. write down the starting checking balance. then run each of the open tickets until it is resolved. Once that is done, open up the desk_tickets.html. on each ticket tab update the actual section from the run. highlight which agents worked, what delegated, and the tools they used. do not change anything within the exepected section so we can compare later. on the cash tab itemize money, including the starting checking balance once reset, how cash changed when each ticket was resolved and why (whether pay or purchase and dollar amount), and the ending balance making sure it matches with cash_accounts in database. Wrong math will make me lose points even if the tickets show up as resolved, so make sure it is right. also add a resolved_tickets.json file in the output folder for each ticket, including the id, final status , short outcome, and what each agent contributed and any human approvals. also add resolved_board.html in the output folder, which is a double clickable page with a screen shot of the board showing that each of the tickets is resolved. append real runs to the audit_trails.json file and finish harness.md so it covers the tables, mcp tools, the five agents, api routes, the dashboard, and safety rules.

**Missing from the first prompt:** It didn't give the run steps or deliverables, so this asks for a reset and recorded starting balance, running every ticket to resolution, filling in the Actual sections and Cash tab of `desk_tickets.html` with exact math, plus `output/resolved_tickets.json`, `output/resolved_board.html` with a board screenshot, real runs in the audit trail, and a finished `harness.md`.

---

## Part 10: Reflections

### Prompt 1

> move onto part 10

### Prompt 2

> ok we are going to add information to the reflection part of the desk_tickets.html file

**Missing from the first prompt:** It didn't say what the part was about, so this sets the topic (filling in the Reflections tab of `desk_tickets.html`).

### Prompt 3

> for this reflection, I want to include the following information. I will provide some my thoughts, but go on and add details and be thorough. Also be sure to tie every answer specifically to this app and the three run tickets. Use the information on the tickets and cash tabs of the html to add additional details. Any generic AI essays will receive low points. 
>
> Info for reflection:
> 1) how would you evaluate the performance of the agents on each ticket and why
>
> 2) for each ticket how did actual compare to the expected?
>
> 3)what would have been simpler with one agent with tools and why?
>
> 4) describe three new problems campus customs might face that this agent team could solve with the tools built
>
> 5) Describe three new problems the campus customs team might face that this team of agents and tools would not be able to solve, and explain the tools and agents would need in order to solve it.

**Missing from the first prompt:** It didn't say what the reflection should cover, so this lists five questions (per-ticket performance, Expected vs. Actual, what one agent would simplify, three problems the team can solve, three it can't and what it would need) and requires every answer to be specific to this app and the three runs.

### Prompt 4

> this reflections html should be put into the reflection stab in the the desk_tickets.html

**Missing from the first prompt:** It didn't say where the reflection should live, so this confirms it belongs inside the Reflections tab of `desk_tickets.html`, not in a separate file.

### Prompt 5

> For question 1, I think my main feedback is that the agents were surprisingly expense and not particularly quick. I think there was also a lot of discussing between agents. Hwoever, ultimately reached the final and correct findings for each of the tickets.

**Missing from the first prompt:** It didn't give the author's own view, so this adds the main takeaway for question 1: the agents were expensive, slow and talked to each other a lot, but reached the correct findings on every ticket.

### Prompt 6

> Question two looks good to me. for question three about one agent with tools. I think the main take away similar to point 1 is that it would have required a lot less dialogue and tokens to accomplish some very simple tickets. The agents re-asked for a lot of information, while one agent woul dbe a lot more efficient.

**Missing from the first prompt:** It didn't give the author's view on questions 2 and 3, so this approves question 2 and adds the main takeaway for question 3: one agent would have needed far less dialogue and far fewer tokens, because the agents kept re-asking for the same information.

### Prompt 7

> there is an uncaught error, what is that from?

**Missing from the first prompt:** It didn't mention any errors, so this asks where an uncaught error on the dashboard comes from.

### Prompt 8

> it still shows the error

**Missing from the first prompt:** It didn't say the first fix hadn't worked, so this reports the error is still showing after the dashboard fixes.

---

## Part 11: Pushing to GitHub

### Prompt 1

> ok that error went away, lets move onto part 11

### Prompt 2

> this is going to be pushig the info to a github repo, do nothing wiht that

**Missing from the first prompt:** It didn't say what the part was about, so this sets the topic (pushing the project to a GitHub repo) and says to wait for instructions.

### Prompt 3

> create a README.md file. this should explain copy original database to the working copy when need a run, start mcp server, start fastapi backend, start react board, reset db before a full three-ticket run.

**Missing from the first prompt:** It didn't say what the repo needs, so this asks for a `README.md` explaining how to copy the original database to the working copy, start the MCP server, start the FastAPI backend, start the React board, and reset the database before a full three-ticket run.

### Prompt 4

> ok create at the top the hw5 folder. Here is what the file branch should look like. Do not include the .env and instead create the example.env. also, once we push it to github, add the url to github_url.txt .  let me know if there is any file missing.
>
> [Image: folder tree for hw5/ showing AI_prompts.md, requirements.txt, .env.example, .gitignore, .mcp.json, README.md, data/, mcp_server/, frontend/, backend/ (main.py, models.py, prompts/), and output/ (harness.md, mcp_smoke.json, desk_tickets.html, design.md, resolved_tickets.json, resolved_board.html, audit_trail.json, github_url.txt)]

**Missing from the first prompt:** It didn't give the repo layout, so this asks for an `hw5/` folder matching a given tree, with `.env.example` instead of `.env`, an `output/github_url.txt` to fill in after pushing, and a check for missing files.
