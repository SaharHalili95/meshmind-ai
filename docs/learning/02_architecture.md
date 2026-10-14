# 2️⃣ ארכיטקטורה

> ארכיטקטורה מוצגת בכמה **רמות זום**, כמו מפה. נתחיל מהתמונה הגדולה ונרד עד רמת
> המחלקה והפונקציה. השיטה נקראת **מודל C4** (Context → Containers → Components → Code).

[⬅ חזרה לאזור הלמידה](README.md)

---

## 2.1 רמה 1: הקשר המערכת (System Context)

מי משתמש במערכת, ומה נכנס ויוצא ממנה.

```mermaid
flowchart LR
    R(["👩‍💻 חוקר/ת / מפתח/ת"])
    C["📄 configs/default.yaml<br/><i>היפר-פרמטרים, טופולוגיה, תעבורה</i>"]
    M["🧠 <b>MeshMind AI</b><br/>סימולטור רשת + סוכן Q-learning<br/>+ מנוע ניסויים"]
    O["📊 results/<br/><i>summary.json · CSV · PNG</i>"]
    G["🌐 GitHub / LinkedIn<br/><i>README + גרפים</i>"]

    R -- "make experiments<br/>python -m meshmind.cli" --> M
    C -- "נטען ומאומת" --> M
    M -- "כותב" --> O
    O -- "מוצג ב" --> G

    style M fill:#2a78d6,stroke:#1a4f8f,color:#ffffff
    style C fill:#f4f4f2,stroke:#a3a29c,color:#0b0b0b
    style O fill:#f4f4f2,stroke:#a3a29c,color:#0b0b0b
    style G fill:#f4f4f2,stroke:#a3a29c,color:#0b0b0b
    style R fill:#ffffff,stroke:#52514e,color:#0b0b0b
```

---

## 2.2 רמה 2: מכולות (Containers)

ארבעה "גושים" לוגיים, כל אחד עם אחריות אחת.

```mermaid
flowchart TB
    subgraph IF["🖥️ ממשק"]
        CLI["cli.py<br/>5 פקודות"]
        SCR["scripts/run_experiments.py"]
    end

    subgraph ORC["🎛️ תזמור ניסויים"]
        EXP["experiments.py<br/>לולאת seeds, צבירה, שמירה"]
        PLT["plotting.py<br/>5 גרפים"]
    end

    subgraph LRN["🧠 למידה והחלטה"]
        AG["agent.py<br/>QLearningAgent"]
        BS["baselines.py<br/>SP · CA · Random"]
        TR["training.py"]
        EV["evaluation.py"]
    end

    subgraph SIM["🌐 סימולציה"]
        ENV["environment.py<br/>NetworkEnvironment"]
        TOP["topology.py<br/>NetworkTopology"]
        TRF["traffic.py<br/>TrafficGenerator"]
        MET["metrics.py<br/>MetricsTracker"]
    end

    CFG[("config.py<br/>dataclasses")]

    IF --> ORC
    ORC --> LRN
    LRN --> SIM
    CFG -.-> ORC
    CFG -.-> SIM
    CFG -.-> AG

    style IF fill:#f4f4f2,stroke:#52514e,color:#0b0b0b
    style ORC fill:#fdf3e1,stroke:#eda100,color:#0b0b0b
    style LRN fill:#e8f1fc,stroke:#2a78d6,color:#0b0b0b
    style SIM fill:#e6f6ef,stroke:#1baf7a,color:#0b0b0b
```

**כלל הזהב:** חיצים יורדים **רק למטה**. שכבה תחתונה לא מכירה שכבה עליונה. לכן אין
תלויות מעגליות, וכל שכבה נבדקת לבד.

---

## 2.3 רמה 3: גרף תלויות מדויק בין מודולים

הגרף נבנה מתוך שורות ה-`import` בקוד:

```mermaid
flowchart BT
    config
    topology
    traffic
    metrics
    environment --> config
    environment --> metrics
    environment --> topology
    environment --> traffic
    agent --> config
    baselines --> environment
    baselines --> topology
    training --> agent
    training --> environment
    training --> metrics
    evaluation --> agent
    evaluation --> environment
    evaluation --> metrics
    experiments --> agent
    experiments --> baselines
    experiments --> config
    experiments --> environment
    experiments --> evaluation
    experiments --> metrics
    experiments --> topology
    experiments --> traffic
    experiments --> training
    plotting
    cli --> experiments
    cli --> plotting
    cli --> agent
    cli --> config
    cli --> evaluation
    cli --> metrics
    cli --> training

    classDef l0 fill:#e6f6ef,stroke:#1baf7a,color:#0b0b0b
    classDef l1 fill:#e8f1fc,stroke:#2a78d6,color:#0b0b0b
    classDef l2 fill:#fdf3e1,stroke:#eda100,color:#0b0b0b
    classDef l3 fill:#fdeee7,stroke:#eb6834,color:#0b0b0b
    class config,topology,traffic,metrics l0
    class environment,agent l1
    class baselines,training,evaluation l2
    class experiments,plotting,cli l3
```

> 💡 שימו לב ש-`agent` תלוי **רק** ב-`config`. זה מה ש-ADR-4 מבטיח: הסוכן נייד לגמרי.
> `plotting` לא תלוי באף מודול פנימי. הוא קורא רק קבצים מהדיסק.

---

## 2.4 רמה 4: דיאגרמת מחלקות (UML)

```mermaid
classDiagram
    direction LR

    class NetworkTopology {
        +str name
        +DiGraph graph
        +float max_utilization
        +from_name(name) NetworkTopology$
        +neighbors(node) list~int~
        +add_load(u, v, amount)
        +decay_loads(factor)
        +reset_loads()
        +edge_cost(u, v) float
        +delivery_fraction(u, v) float
        +outgoing_utilization(node) float
        +average_utilization() float
    }

    class TrafficGenerator {
        +ndarray nodes
        +str profile
        +Generator rng
        +generate(count, seed) list~Flow~
        +reseed(seed)
    }

    class Flow {
        <<frozen dataclass>>
        +int source
        +int destination
        +float demand
    }

    class NetworkEnvironment {
        +NetworkTopology topology
        +TrafficGenerator traffic
        +EnvironmentConfig config
        +list~Flow~ flows
        +list~int~ path
        +bool episode_done
        +reset(seed, flows) State
        +get_observation() State
        +get_valid_actions(state) list~int~
        +step(action) StepResult
    }

    class QLearningAgent {
        +dict q_table
        +float alpha
        +float gamma
        +float epsilon
        +bool eval_mode
        +select_action(state, actions) int
        +greedy_action(state, actions) int
        +update(s, a, r, s2, actions2, done) float
        +decay_epsilon() float
        +set_eval_mode(enabled)
        +save(path)
        +load(path) QLearningAgent$
    }

    class RoutingPolicy {
        <<Protocol>>
        +str name
        +reset(seed)
        +select_action(env, state, actions) int
    }

    class ShortestPathBaseline
    class CongestionAwareBaseline
    class RandomRoutingBaseline

    class MetricsTracker {
        +list~FlowResult~ flows
        +record_flow(result)
        +record_utilization(value)
        +pdr float
        +plr float
        +summary() dict
    }

    class FlowResult {
        <<frozen dataclass>>
        +float offered_demand
        +float delivered_demand
        +float latency_ms
        +int hops
        +bool success
        +str failure_reason
    }

    NetworkEnvironment *-- NetworkTopology : owns
    NetworkEnvironment *-- TrafficGenerator : owns
    TrafficGenerator ..> Flow : creates
    NetworkEnvironment ..> FlowResult : emits
    MetricsTracker o-- FlowResult : collects
    RoutingPolicy <|.. ShortestPathBaseline
    RoutingPolicy <|.. CongestionAwareBaseline
    RoutingPolicy <|.. RandomRoutingBaseline
    RoutingPolicy ..> NetworkEnvironment : reads
```

### דפוסי עיצוב (Design Patterns) בפרויקט

| דפוס | איפה | למה |
|---|---|---|
| **Strategy** | `RoutingPolicy` + 3 baselines | אותה לולאת הערכה (`run_policy`) לכל מדיניות |
| **Adapter** | `evaluate_agent` עוטף את הסוכן ב-`act()` | הסוכן לא מכיר את `env`, אבל נכנס לאותה לולאה |
| **Factory method** | `NetworkTopology.from_name()` | יצירת טופולוגיה מוכרת לפי שם |
| **Value Object** | `Flow`, `FlowResult`, כל ה-Configs (`frozen=True`) | אי-שינוי: אי אפשר לשנות בטעות תוצאה שכבר נרשמה |
| **Protocol (duck typing)** | `RoutingPolicy` | חוזה מפורש בלי ירושה |

---

## 2.5 מחזור החיים של זרימה (State Machine)

כל זרימה עוברת את המצבים האלה בתוך `env.step()`:

```mermaid
stateDiagram-v2
    [*] --> AtSource: reset() / _start_flow()

    AtSource --> Hopping: פעולה חוקית
    Hopping --> Hopping: פעולה חוקית<br/>(לא יעד, לא לולאה, k < 20)

    AtSource --> Failed_Invalid: שכן לא קיים
    Hopping --> Failed_Invalid: שכן לא קיים
    Hopping --> Failed_Loop: ביקור חוזר או מבוי סתום
    Hopping --> Failed_MaxSteps: k = 20
    AtSource --> Delivered: הגיע ליעד
    Hopping --> Delivered: הגיע ליעד

    Delivered --> NextFlow: +10 תגמול
    Failed_Invalid --> NextFlow: ‎-100, בלי שינוי עומס
    Failed_Loop --> NextFlow: ‎-100
    Failed_MaxSteps --> NextFlow: ‎-100

    NextFlow --> AtSource: יש עוד זרימות<br/>(עומס × 0.85)
    NextFlow --> [*]: episode_done = True

    note right of Hopping
        בכל hop:
        load += demand
        reward = -0.1·cost - 50·dropped
    end note
```

---

## 2.6 רצף פעולות: צעד אחד (`step`)

```mermaid
sequenceDiagram
    autonumber
    participant P as Policy (Agent / Baseline)
    participant E as NetworkEnvironment
    participant T as NetworkTopology
    participant M as MetricsTracker

    P->>E: get_valid_actions(state)
    E->>T: neighbors(current)
    T-->>E: [n1, n2, n3]
    E-->>P: שכנים שלא בוקרו
    P->>P: select_action → a
    P->>E: step(a)
    alt a לא שכן
        E-->>P: (state, -100, done=True, info)
    else a שכן חוקי
        E->>T: add_load(current, a, demand)
        T->>T: עדכון utilization ו-penalty
        E->>T: edge_cost(), delivery_fraction()
        T-->>E: cost, φ
        E->>E: reward = -0.1·cost - 50·Δφ
        E->>E: בדיקות: יעד? לולאה? מבוי סתום? k=20?
        E-->>P: (next_state, reward, done, info)
    end
    opt done = True
        P->>M: record_flow(info["flow_result"])
        P->>M: record_utilization(info["avg_utilization"])
        E->>T: decay_loads(0.85)
    end
```

---

## 2.7 זרימת נתונים: ניסוי מלא

```mermaid
flowchart LR
    Y["default.yaml"] -->|load_config| C["ExperimentConfig"]
    C --> L{{"for seed in<br/>42, 100, 2026"}}

    L --> B["build_environment"]
    B --> TR["train_agent<br/>3000 episodes<br/>seeds s..s+2999"]
    TR --> H[("history<br/>per episode")]
    TR --> Q[("Q-table")]

    Q --> EA["evaluate_agent<br/>ε=0, read-only"]
    B --> EB["evaluate_policy × 3<br/>baselines"]
    EA --> R[("metrics per<br/>seed × policy")]
    EB --> R

    subgraph HELD["🔒 seeds מוחזקים בצד: s+10⁶ ... s+10⁶+99"]
        EA
        EB
    end

    R --> AGG["aggregate_metrics<br/>mean ± std (ddof=1)"]
    AGG --> S["summary.json"]
    R --> PS["per_seed_results.csv"]
    H --> TH["training_history.csv"]
    S --> PL["plotting"]
    TH --> PL
    PL --> F["5 × PNG"]

    style HELD fill:#fdf3e1,stroke:#eda100,color:#0b0b0b
    style S fill:#e6f6ef,stroke:#1baf7a,color:#0b0b0b
    style PS fill:#e6f6ef,stroke:#1baf7a,color:#0b0b0b
    style TH fill:#e6f6ef,stroke:#1baf7a,color:#0b0b0b
    style F fill:#e6f6ef,stroke:#1baf7a,color:#0b0b0b
```

---

## 2.8 הטופולוגיה: רשת Abilene

רשת Abilene הייתה רשת ה-backbone האקדמית של ארה"ב (Internet2). המספרים על הקישורים
הם השהיית התפשטות במילישניות.

```mermaid
flowchart LR
    STTL["0 Seattle"] ---|6.5| SNVA["1 Sunnyvale"]
    STTL ---|8.2| DNVR["3 Denver"]
    SNVA ---|2.9| LOSA["2 Los Angeles"]
    SNVA ---|7.8| DNVR
    LOSA ---|11.0| HSTN["5 Houston"]
    DNVR ---|4.6| KSCY["4 Kansas City"]
    KSCY ---|5.9| HSTN
    KSCY ---|4.8| IPLS["6 Indianapolis"]
    HSTN ---|6.0| ATLA["7 Atlanta"]
    IPLS ---|"1.4 · cap 80"| CHIN["8 Chicago"]
    IPLS ---|3.8| ATLA
    CHIN ---|5.7| NYCM["9 New York"]
    NYCM ---|"1.7 · cap 80"| WASH["10 Washington"]
    WASH ---|4.9| ATLA
    ATLA ---|"0.2 · cap 150"| ATM5["11 Atlanta-M5<br/>(leaf)"]

    style ATM5 fill:#fdeee7,stroke:#eb6834,color:#0b0b0b
    style KSCY fill:#e8f1fc,stroke:#2a78d6,color:#0b0b0b
    style ATLA fill:#e8f1fc,stroke:#2a78d6,color:#0b0b0b
```

* **צמתים כחולים** הם צמתי מעבר מרכזיים (degree 3-4), שם הסוכן מקבל את ההחלטות
  המשמעותיות.
* **הצומת הכתום** הוא עלה (leaf) עם שכן אחד בלבד. הוא היה המקור לתקלה #14.
* קיבולת ברירת המחדל היא 100. קישורים עם קיבולת אחרת מסומנים.

---

## 2.9 מבנה הקבצים: מי אחראי על מה

```
meshmind-ai/
├── configs/default.yaml          ← כל המספרים "הקסומים" במקום אחד
├── src/meshmind/
│   ├── config.py                 ← שכבה 0: dataclasses + ולידציה
│   ├── topology.py               ← שכבה 0: גרף + מצב קישורים
│   ├── traffic.py                ← שכבה 0: יצירת זרימות
│   ├── metrics.py                ← שכבה 0: חישוב מדדים
│   ├── environment.py            ← שכבה 1: MDP (state/action/reward)
│   ├── agent.py                  ← שכבה 1: Q-learning (בלי תלות בסביבה!)
│   ├── baselines.py              ← שכבה 2: מדיניות להשוואה
│   ├── training.py               ← שכבה 2: לולאת אימון
│   ├── evaluation.py             ← שכבה 2: לולאת הערכה (read-only)
│   ├── experiments.py            ← שכבה 3: תזמור רב-seed
│   ├── plotting.py               ← שכבה 3: גרפים מקבצים
│   └── cli.py                    ← שכבה 4: ממשק משתמש
├── tests/                        ← בדיקה לכל מודול + conftest משותף
├── docs/                         ← תיעוד טכני (EN) + אזור למידה (HE)
└── results/                      ← פלטים (Q-tables לא נשמרים ב-git)
```

[⬅ תכנון](01_project_planning.md) · [המשך ← תקלות ופתרונות](03_troubleshooting.md)
