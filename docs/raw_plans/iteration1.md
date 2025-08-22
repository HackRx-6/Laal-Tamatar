# Project Iterations

We have split our project into “iterations” for each major phase of development and submissions.

---

## Iteration 1

**Goal:**  
Simple Agent to solve dynamic web page requests + retrieval of what request questions may look like

---

### Stuff Used:
- LangGraph - Agent Building  
- LangSmith - monitoring  
- Puppeteer  

**Tools given to the agent:**
- curl  

**What the agent receives as context:**
- Website context received from a headless browser instance  

---

### What we’re trying to handle:
- Differentiate between server and client side rendered websites  
  - Judging Request headers  
  - Too much JS on the pages?  
- Media handling  
- Prompt injections, question instructions v/s webpage contexts  

---

### Final decisions:
- Will go entirely with a headless browser since we don’t know what the test cases really look like  
- The Agent will be able to inject JavaScript into the headless browser  
- (after struggling with placeholder base64): submitting a tiny logger to log question bodies.  
