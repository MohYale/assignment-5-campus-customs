# AI Prompts

This file is a log of the prompts used for Assignment 5. Each section is one problem: the problem number and title, the prompt used, and any follow-up prompts under that same heading.

---

## Problem 1 — Vibe coder prompts

### Prompt

I want to start my AI assignment now. First I want to use GPT-6-luna for this assignment. I want you to unzip data.zip in this folder. I want you to create an AI_prompts.md file that contains my prompts. I want these prompts to be filed under a heading. This is problem 1: Vibe coder prompts. Put this prompt under this title.

---

## Problem 2 — Staudy the campus customs database

### Prompt

We will start problem 2: Staudy the campus customs database. I want you to open data/campus_customs.db and look through every table and its fields. I want you to compy the original file to data/campus_customs_new.db. There are three open tickets in this database. Show it to me in a tabular form so that I can understand how they link to the other tables. I want to create a file output/harness.md. For each table, I want you to list the fields and one short line on why the table matters for the agents we will be creating.

---

## Problem 3 — Build the MCP server

### Prompt

We will start problem 3: Build the MCP server. We will write and MCP server in mcp_server and we will use fastmcp. I want it to talk to data/campus_customs_new.db. I will be creating agents in this assignment and every agent I create will be using the MCP server that we will build. I want to write three tools that I will need for these open tickets. Tool 1: Assess the request of the ticket. See where we can answer their request. What are they asking us to provide? Which dataset/file would be helpful to complete their request, Tool 2: Do we have what they are asking in our inventory, Tool 3: If we have the item, did we get paid for it in full? Tool 4: If we do not have it in inventory, do not accept the payment and email the customer that we will contact you when item becomes available. Then I want you to contact the providers to see if they can restock our inventory to meet the demands of our customer. After that, I want you list each of the MCP tools in output/harness.md. For each tool, I want you to include which table it reads, which ticket it helps unlock (101, 102, 103) andone sentence on why that tool is the right one for that ticket. I also want you to add a short mcp_server/readme.md file that explains what the MCP server is for which database file it uses and the tools it has.

---

## Problem 4 — Add the MCP server to vibe coder and test each tool

### Prompt

We will start problem 4: Add the MCP server to vibe coder and test each tool. I want you to add the MCP server we created to this project so that claudecoder can call the tools. I want you to save the connection JSOn text in .mcp.json at the project root; whichever clause usually save local MCP server lists. Once you connect the Claude coder, I want you to test each of the tools we created in the MCP tools. Save the evidence in output/mcp_smoke.json. For every tool I want you to include: 1) the prompt we asked, 2) the tool name, 3) the tool output (this must match values in data/campus_customs_new.db

---

## Problem 5 — build the agent team and grow the MCP tools

### Prompt

Now we will start problem 5: build the agent team and grow the MCP tools. I want to build a team of agents to help Campus customs using the PydanticAI. I want to build five agents: Boss, inventory, accounting, facilities, and customer services. I want to include prompts, models and agent loops so that these agents delegate tasks among them with full connectivity. I want you to put the agent prompts in backend/prompts/ and I want one file per agent. I want you to put data types in backend/models.py and the agent files under backend/. I hope that you are still using gpt-6-luna for this assignement. These are the tools that we will give these agents. First, I want to boss agent to read each ticket and I want it to decide which agent it will delegate the task to. I also want this agent to make final calls. I want the inventory agent to check the stock by SKU and size. i want it to see where he have shortages and I want it to figure out which vendor it needs to restock the deficient items. Next, I want the accounting agent to watch cash and invouces, check margins, and prepares payments or purchase orders for human approval. Then, I want the facilities agent to handle the shop space side (leases, rent, etc) and I want the customer service agent to draft messages for customer. I want you to add any tool the agents need to use the MCP server so they can work togeter on the open tickets. Shop facts come from the MCP server over data/campus_customs_new.db. I do not want you to invent a second shop tools layer that bypasses MCP. I want you to wire the agents so they append to output/audit_trail.json as they run: for each agent-loop step record enought to audit later. Append to this file - do not wipe it each run. In output/harness.md, list each agent and each MCP tool (including ones you add in this problem) along with which table the tool uses. Also add a short safety section: this should contain a check with me before any transection/money movement is completed. I do not any emails/phone calls go to the customers without checking with me. I want you to update the mcp_server/readme.md so the tool list matches what I have now.

---

## Problem 6 — plan the three tickets

### Prompt

Now we will do problem 6: plan the three tickets.  I want you to build output/desk_tickets.html - a page you can double-click with one tab per ticket (101, 102, 103). Also add empty cash and reflection tabs for later problems (leave them with a short " coming later" note for now. On each ticket tab, fill an expected section only (leave rooom for an actual section that we will fill after we run the agents). For each ticket's expected section I want to write down the following: 1) who the boss should call first and why, 2) All the agent delegations I would expect, 3) Which MCP tools I expect that run to use. I want to compare this plan to what actually happens when we run the agents. For ticket 1: The boss agent will see that customer Tauhid Zaman want 1 cc-TEE-white in size S. This will send this request to the inventory agent to check if we have this item. We will find that we do not and it should see which vendor we should contact to restock this item. It will tell the boss agent. I expect the boss agent to delegate to the accounting agent to see if we have enough cash to buy it from the vendor which will tell the boss agent we do, Then the boss agent will talk to customer service agent to draft an email to customer Tauhid zaman telling him that the item he wants is not in stock and we will work to get it expecting 5 days. We will email him with updates. For ticket 2: I expect the boss agent to see that this is a rent ticket and to delegate the task to accounting agent. I expect the accounting agent to assess our checking account and to realize that we have enough money to pay the rent. It will prepare the payment and will make it available to the boss which will deleagte to the facilities agent which handles the rent. ticket 3: I expect the boss agent to realize that this is a purchase of 20 * cc-hood-navy in size M. I expect it to delegate to the inventory agent and this agent will see that we have only 8. This agent will figure out that we need to contact the vendor to ge the remainder of what is needed. This will tell the boss agent which will tell the accounting agent to make sure we have enough fund to buy the rest of what is needed. The boss will be told that we do. The boss will delegate to customer service to draft an email explaining the currrent situation to the customer with updates when the purchase will become available.

---

## Problem 7 — backend routes

### Prompt

Now we will do problem 7: backend routes. We will create a fronend dashboard using react later in this assignemnt. First, in backend/main.py, use fastapi and add routes that do the following: 1) return the three tickets and whether each is oper or resolved, 2) take a ticket id and run our agent team on that ticket, 3) return recent agent events (what each agent said and which tools they used) so the board can refresh, 4) approve a payment or purchase after a human clicks approve (agents only prepare the pay; this route is what actually changes cash), 5) return the current checking balance from cash_accounts 6) reset the database to the original values when you want to try a fresh run. From backend/ folder, start the server with : uvicorn main:app --reload --port 8000. In output/harness.md, list each route in one line (what URL/what it does).

---

## Problem 8 — agent dashboard

### Prompt

Now we will do problem 8: agent dashboard. We will build the frontend dashboard in frontend/ with reacht, Vite and typescript. The page should call the routes we built in problem 7. At minimum, the boad should: 1) list all three tickets, 2) let you pick one ticket and start the agent team on it, 3) show each agent and what they are saying/doing while the ticket runs, 4) mark a ticket resolved when the run finished 5) show a short summary of what each agent did on that ticket, 6) let a human approve a pay or purchase when asked, 7) show the checking balance (it should drop after an approved pay). I want the dashboard to look good. Style it with picture from Yale univeristy such as the Harkness tower, Evans hall, other colleges, etc. I also want pictures of the handsome dan Yale mascot. I want to create a diagram of the agents represented as mesopotamian winged bulls. The boss agent at top and connected to the other agents below him. I want to see how the though chain occur as they resolve a ticket. I want the front end to talk to the backend at http://localhost:8000. On the backend, allow the vite page origin (usually: http://localhost:5173) so the browser is allowed to call those routes. Start the board with: npm run dev. I want you to write output/design.md with what I chose for the dashboard look.

---

## Problem 9 — resolve the tickets

### Prompt

We will start problem 9: resolve the tickets. I want to reset the working databse data/campus_customs_new.db so we can start clean. Then I want you to run the three tickets on the board (101, 102, 103) until each is resolved. I want you to open output/desk_tickets.html from problem 6. on each ticket tab, I want you to fill the actual section from this run: which agents worked, what they delegated, and which tools they used. Keep your expected section so I can compare the two. On the cash tab of the same output/desk_tickets.html, i want you to itemize the money: Starting checking balance (after the reset), for each ticket, how cash changed when that ticket ersolved, and why (which pay/purchase, dollar amount) and ending checking balance (it must match cash_accounts in the working database. I also want you to save: output/resolved_tickets.json - for each ticket: ID, final status, short outcome, what each agent contributed and any human approvals; output/resolved_board.html - a page where I can double click with a screenshot of my React board for each resolved ticket (101, 102, 103). Append real runs to output/audit_trail.json. I want you to finish output/harness.md so it covers tables, MCP tools, the five agents, API routes, the dashboard, and safety rules.

---

## Problem 10 — reflection

### Prompt

We will start problem 10: reflection. Make sure this is included in the ai_prompt.md file. I want you to open output/desk_tickets.html and fill the reflection tab. I want you include the following: 1) How would you evaluate the performance of the agents on each ticket and why? I feel that they did excellent job. they were able to perform the tasks to my expectations. 2) For each ticket, compare the expected plan that I wrote to the actual excuted plan. 3) What would have been simpler as one agent with tools and why? These tasks remain simple and do not have a degree of complexity to have multi-level agent. 4) Three new problems that this team agents could handle; a) They can do similar tickets for different inventory on Campus Customs, b) It can handle updating the current checking account and keep it clean/simple c) These agents can handle if a customer asks for discount, 5) Things that this multiagent team cannot handle; a) For ticket 3, we had 8 hoodies and we were going to order 12 but these orders do not change the inventory. I would add a tool that would count these units to the shelf. b) I would improve the customer service agent by adding email and phone number to improve experience, c) If a discount is offered, I would add a tool to adjust the price of the item to the discounted price.

---
