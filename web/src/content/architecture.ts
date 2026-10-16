import type { Localized } from './localized'

export type NodeId =
  | 'cli' | 'script'
  | 'experiments' | 'plotting'
  | 'training' | 'evaluation' | 'agent' | 'baselines'
  | 'environment' | 'topology' | 'traffic' | 'metrics'
  | 'config' | 'results'

export interface Lane {
  id: string
  title: Localized
  role: Localized
}

export interface DiagramNode {
  id: NodeId
  lane: number
  row: number
  label: string
  plain: Localized
  api: string
  code: string
  test?: string
}

export interface FlowStep {
  node: NodeId
  text: Localized
}

export interface Flow {
  id: string
  title: Localized
  summary: Localized
  steps: FlowStep[]
}

export const lanes: Lane[] = [
  { id: 'interface', title: { en: 'Interface', he: 'ממשק' },
    role: { en: 'How a person starts a run: CLI commands and the benchmark script.', he: 'איך מפעילים הרצה: פקודות CLI וסקריפט הניסוי.' } },
  { id: 'orchestration', title: { en: 'Orchestration', he: 'תזמור' },
    role: { en: 'Runs every seed, aggregates mean ± std, writes files and draws the figures.', he: 'מריץ את כל ה-seeds, מחשב ממוצע ± סטיית תקן, כותב קבצים ומצייר גרפים.' } },
  { id: 'learning', title: { en: 'Learning & decisions', he: 'למידה והחלטות' },
    role: { en: 'The Q-learning agent, the three baselines, and the train and evaluate loops.', he: 'סוכן ה-Q-learning, שלושת ה-baselines, ולולאות האימון וההערכה.' } },
  { id: 'simulation', title: { en: 'Simulation', he: 'סימולציה' },
    role: { en: 'The network itself: links, traffic, the MDP rules and the metrics.', he: 'הרשת עצמה: קישורים, תעבורה, חוקי ה-MDP והמדדים.' } },
  { id: 'data', title: { en: 'Config & data', he: 'הגדרות ונתונים' },
    role: { en: 'Typed configuration in, reproducible result files out.', he: 'הגדרות עם טיפוסים נכנסות, קבצי תוצאות משוחזרים יוצאים.' } },
]

export const nodes: DiagramNode[] = [
  { id: 'cli', lane: 0, row: 0, label: 'cli.py', api: 'smoke-test · train · evaluate · experiments · plot', code: 'src/meshmind/cli.py', test: 'tests/test_experiments.py',
    plain: { en: 'Five commands for everything you can do with the project. Errors become a clear message and exit code 1.', he: 'חמש פקודות לכל מה שאפשר לעשות בפרויקט. שגיאות הופכות להודעה ברורה ולקוד יציאה 1.' } },
  { id: 'script', lane: 0, row: 1.2, label: 'run_experiments.py', api: 'make experiments', code: 'scripts/run_experiments.py',
    plain: { en: 'One command that runs the full benchmark and regenerates every figure.', he: 'פקודה אחת שמריצה את כל הניסוי ומייצרת מחדש את כל הגרפים.' } },
  { id: 'experiments', lane: 1, row: 0, label: 'experiments.py', api: 'run_experiment_pipeline(config)', code: 'src/meshmind/experiments.py', test: 'tests/test_experiments.py',
    plain: { en: 'For each seed: build a fresh network, train a fresh agent, evaluate it and the baselines on the same held-out traffic, then aggregate.', he: 'לכל seed: בונה רשת חדשה, מאמן סוכן חדש, ובוחן אותו ואת ה-baselines על אותה תעבורה מוחזקת בצד, ואז מסכם.' } },
  { id: 'plotting', lane: 1, row: 1.2, label: 'plotting.py', api: 'generate_all_plots(results_dir)', code: 'src/meshmind/plotting.py', test: 'tests/test_experiments.py',
    plain: { en: 'Reads only the result files, never the live objects, so figures can be redrawn any time without retraining.', he: 'קורא רק את קבצי התוצאות, אף פעם לא אובייקטים חיים, כך שאפשר לצייר מחדש בכל רגע בלי לאמן שוב.' } },
  { id: 'training', lane: 2, row: 0, label: 'training.py', api: 'train_agent(env, agent, episodes, base_seed)', code: 'src/meshmind/training.py', test: 'tests/test_training.py',
    plain: { en: 'The episode loop: act, observe, update after every hop, decay ε after every episode, and log the history.', he: 'לולאת הפרקים: פעולה, תצפית, עדכון אחרי כל hop, הקטנת ε אחרי כל פרק, ורישום ההיסטוריה.' } },
  { id: 'evaluation', lane: 2, row: 1, label: 'evaluation.py', api: 'evaluate_agent(...) · evaluate_policy(...)', code: 'src/meshmind/evaluation.py', test: 'tests/test_evaluation.py',
    plain: { en: 'Runs any policy through the same loop on held-out seeds. The agent is locked: any Q-table update raises an error.', he: 'מריץ כל מדיניות באותה לולאה על seeds מוחזקים בצד. הסוכן נעול: כל ניסיון לעדכן את ה-Q-table זורק שגיאה.' } },
  { id: 'agent', lane: 2, row: 2, label: 'agent.py', api: 'select_action · update · decay_epsilon', code: 'src/meshmind/agent.py', test: 'tests/test_agent.py',
    plain: { en: 'The Q-table (a dict) and the Bellman update. It knows nothing about networks: only states, actions and rewards.', he: 'ה-Q-table (מילון) ועדכון Bellman. הוא לא יודע כלום על רשתות: רק מצבים, פעולות ותגמולים.' } },
  { id: 'baselines', lane: 2, row: 3, label: 'baselines.py', api: 'ShortestPath · CongestionAware · Random', code: 'src/meshmind/baselines.py', test: 'tests/test_baselines.py',
    plain: { en: 'Three policies to compare against: static Dijkstra, Dijkstra on live global load at every hop, and random.', he: 'שלוש מדיניות להשוואה: Dijkstra סטטי, Dijkstra על עומס גלובלי חי בכל hop, ואקראי.' } },
  { id: 'environment', lane: 3, row: 0, label: 'environment.py', api: 'reset · get_observation · get_valid_actions · step', code: 'src/meshmind/environment.py', test: 'tests/test_environment.py',
    plain: { en: 'The MDP: turns the network into states, masked actions and rewards, and decides when a flow ends.', he: 'ה-MDP: הופך את הרשת למצבים, פעולות מסוננות ותגמולים, ומחליט מתי זרימה מסתיימת.' } },
  { id: 'topology', lane: 3, row: 1, label: 'topology.py', api: 'add_load · edge_cost · delivery_fraction', code: 'src/meshmind/topology.py', test: 'tests/test_topology.py',
    plain: { en: 'The graph and its link state: capacity, latency, load, utilization and the congestion penalty above 80%.', he: 'הגרף ומצב הקישורים: קיבולת, השהיה, עומס, ניצולת ועונש העומס מעל 80%.' } },
  { id: 'traffic', lane: 3, row: 2, label: 'traffic.py', api: 'TrafficGenerator.generate(count, seed)', code: 'src/meshmind/traffic.py', test: 'tests/test_traffic.py',
    plain: { en: 'Creates flows (source, destination, demand) from a profile and a seed. Same seed, same traffic.', he: 'יוצר זרימות (מקור, יעד, ביקוש) לפי פרופיל ו-seed. אותו seed, אותה תעבורה.' } },
  { id: 'metrics', lane: 3, row: 3, label: 'metrics.py', api: 'MetricsTracker · aggregate_metrics', code: 'src/meshmind/metrics.py', test: 'tests/test_metrics.py',
    plain: { en: 'PDR, PLR, latency, throughput, utilization and failures, safe against division by zero.', he: 'PDR, PLR, השהיה, תפוקה, ניצולת וכשלים, מוגן מחלוקה באפס.' } },
  { id: 'config', lane: 4, row: 0, label: 'config.py', api: 'load_config("configs/default.yaml")', code: 'src/meshmind/config.py',
    plain: { en: 'Frozen dataclasses validated on construction. Unknown YAML keys raise an error instead of being ignored.', he: 'Dataclasses קפואים שמאומתים ביצירה. מפתח YAML לא מוכר זורק שגיאה במקום להתעלם ממנו.' } },
  { id: 'results', lane: 4, row: 1.5, label: 'results/', api: 'summary.json · *.csv · figures/*.png', code: 'results/',
    plain: { en: 'Everything a run produces. The tables and charts on this site are generated from these files.', he: 'כל מה שהרצה מייצרת. הטבלאות והגרפים באתר הזה נוצרים מהקבצים האלה.' } },
]

export const flows: Flow[] = [
  {
    id: 'train-step',
    title: { en: 'One training step', he: 'צעד אימון אחד' },
    summary: { en: 'What happens on a single hop while the agent learns.', he: 'מה קורה ב-hop בודד בזמן שהסוכן לומד.' },
    steps: [
      { node: 'training', text: { en: 'train_agent starts episode i with traffic seed s + i and calls env.reset(seed).', he: 'train_agent מתחיל את פרק i עם seed תעבורה s + i וקורא ל-env.reset(seed).' } },
      { node: 'traffic', text: { en: 'The generator draws 25 flows. All link loads are reset to zero.', he: 'המחולל מגריל 25 זרימות. כל עומסי הקישורים מתאפסים.' } },
      { node: 'environment', text: { en: 'get_observation returns (current, destination, bin): bin 0/1/2 from the mean utilization of the current node’s outgoing links.', he: 'get_observation מחזיר (נוכחי, יעד, bin): bin 0/1/2 לפי הניצולת הממוצעת של הקישורים היוצאים מהצומת.' } },
      { node: 'agent', text: { en: 'select_action: with probability ε a random valid neighbour (explore), otherwise the highest Q-value (exploit). Visited neighbours are masked out.', he: 'select_action: בהסתברות ε שכן חוקי אקראי (חקירה), אחרת ה-Q הגבוה ביותר (ניצול). שכנים שכבר בוקרו מסוננים.' } },
      { node: 'environment', text: { en: 'step(action) checks the action is a real neighbour. If not: −100 and the flow ends without touching any load.', he: 'step(action) בודק שהפעולה היא שכן אמיתי. אם לא: −100 והזרימה מסתיימת בלי לגעת בעומס.' } },
      { node: 'topology', text: { en: 'add_load adds the flow’s demand to the link, recomputes utilization and the congestion penalty, and returns the hop cost and the share that survives.', he: 'add_load מוסיף את הביקוש לקישור, מחשב מחדש ניצולת ועונש עומס, ומחזיר את עלות ה-hop ואת החלק שעבר.' } },
      { node: 'environment', text: { en: 'reward = −0.1·cost − 50·dropped. +10 if the flow arrived; −100 on a loop, a dead end or 20 hops.', he: 'reward = −0.1·cost − 50·dropped. ‎+10 אם הזרימה הגיעה; ‎−100 על לולאה, מבוי סתום או 20 hops.' } },
      { node: 'agent', text: { en: 'update applies Q ← Q + α[r + γ·max Q(s′,a′) − Q]. When the flow ended, the future term is exactly 0.', he: 'update מחשב Q ← Q + α[r + γ·max Q(s′,a′) − Q]. כשהזרימה הסתיימה, איבר העתיד הוא בדיוק 0.' } },
      { node: 'metrics', text: { en: 'When a flow ends its FlowResult (delivered demand, latency, hops, failure reason) is recorded.', he: 'כשזרימה מסתיימת נרשם ה-FlowResult שלה (ביקוש שהגיע, השהיה, hops, סיבת כישלון).' } },
      { node: 'training', text: { en: 'After 25 flows: ε ← max(0.05, ε × 0.998), and one history row is logged (reward, TD error, PDR...).', he: 'אחרי 25 זרימות: ε ← max(0.05, ε × 0.998), ונרשמת שורת היסטוריה (reward, TD error, PDR...).' } },
    ],
  },
  {
    id: 'benchmark',
    title: { en: 'Full benchmark run', he: 'הרצת ניסוי מלאה' },
    summary: { en: 'From `make experiments` to the numbers on the Results page.', he: 'מ-`make experiments` ועד המספרים בעמוד התוצאות.' },
    steps: [
      { node: 'script', text: { en: 'make experiments runs scripts/run_experiments.py, which calls the CLI.', he: 'make experiments מריץ את scripts/run_experiments.py, שקורא ל-CLI.' } },
      { node: 'cli', text: { en: 'The experiments command loads the config and starts the pipeline.', he: 'הפקודה experiments טוענת את ההגדרות ומתחילה את הצינור.' } },
      { node: 'config', text: { en: 'configs/default.yaml becomes typed, validated dataclasses: Abilene, high load, seeds 42/100/2026.', he: 'configs/default.yaml הופך ל-dataclasses מאומתים: Abilene, עומס גבוה, seeds 42/100/2026.' } },
      { node: 'experiments', text: { en: 'For each seed: a fresh topology, traffic generator, environment and agent. Nothing is shared between seeds.', he: 'לכל seed: טופולוגיה, מחולל תעבורה, סביבה וסוכן חדשים. שום דבר לא משותף בין seeds.' } },
      { node: 'training', text: { en: '3,000 training episodes (75,000 flows) with traffic seeds s … s+2999.', he: '3,000 פרקי אימון (75,000 זרימות) עם seeds תעבורה s … s+2999.' } },
      { node: 'evaluation', text: { en: 'The frozen agent is scored on 100 held-out episodes with seeds s+10⁶ …, which never appear in training.', he: 'הסוכן הנעול נבחן על 100 פרקים מוחזקים בצד עם seeds s+10⁶ …, שלא מופיעים באימון.' } },
      { node: 'baselines', text: { en: 'Shortest path, congestion-aware and random are scored on exactly the same 100 episodes (a paired comparison).', he: 'Shortest path, congestion-aware ו-random נבחנים על אותם 100 פרקים בדיוק (השוואה מזווגת).' } },
      { node: 'metrics', text: { en: 'aggregate_metrics computes mean and sample std (ddof=1) across the three seeds.', he: 'aggregate_metrics מחשב ממוצע וסטיית תקן מדגמית (ddof=1) על פני שלושת ה-seeds.' } },
      { node: 'results', text: { en: 'summary.json, per_seed_results.csv and training_history.csv are written.', he: 'נכתבים summary.json, per_seed_results.csv ו-training_history.csv.' } },
      { node: 'plotting', text: { en: 'Five figures are drawn from the files. The same files feed this website.', he: 'חמישה גרפים מצוירים מהקבצים. אותם קבצים מזינים את האתר הזה.' } },
    ],
  },
]
