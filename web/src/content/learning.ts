import type { Localized } from './localized'

export interface Concept {
  term: string
  text: Localized
  code: string
}

export const concepts: Concept[] = [
  { term: 'State', code: 'environment.get_observation()',
    text: { en: 'What the agent sees: (current router, destination, load level 0/1/2 of the current router’s outgoing links).', he: 'מה שהסוכן רואה: (נתב נוכחי, יעד, רמת עומס 0/1/2 של הקישורים היוצאים מהנתב).' } },
  { term: 'Action', code: 'environment.get_valid_actions()',
    text: { en: 'Which neighbour to forward the flow to next. Neighbours already on the path are masked out.', he: 'לאיזה שכן להעביר את הזרימה עכשיו. שכנים שכבר במסלול מסוננים.' } },
  { term: 'Reward', code: 'environment.step()',
    text: { en: 'A number that grades the action: minus latency, minus dropped traffic, +10 on arrival, −100 on failure.', he: 'מספר שנותן ציון לפעולה: מינוס השהיה, מינוס תעבורה שאבדה, ‎+10 בהגעה, ‎−100 בכישלון.' } },
  { term: 'Q(s, a)', code: 'agent.q_table',
    text: { en: 'The agent’s estimate of the total future reward if it takes action a in state s and then acts well.', he: 'ההערכה של הסוכן לסך התגמול העתידי אם יבצע את הפעולה a במצב s ואחר כך יפעל היטב.' } },
  { term: 'Bellman update', code: 'agent.update()',
    text: { en: 'Moves Q(s,a) a step of size α toward r + γ·max Q(s′,·). After a terminal step the future part is 0.', he: 'מזיז את Q(s,a) צעד בגודל α לכיוון r + γ·max Q(s′,·). אחרי צעד סופי חלק העתיד הוא 0.' } },
  { term: 'ε-greedy', code: 'agent.select_action()',
    text: { en: 'With probability ε try a random action (explore), otherwise take the best known one (exploit). ε shrinks each episode.', he: 'בהסתברות ε לנסות פעולה אקראית (חקירה), אחרת לבחור את הטובה ביותר שידועה (ניצול). ε קטן בכל פרק.' } },
  { term: 'Utilization ρ', code: 'topology.add_load()',
    text: { en: 'Load divided by capacity. Above 0.8 a quadratic congestion penalty starts; above 1.0 traffic is dropped.', he: 'עומס חלקי קיבולת. מעל 0.8 מתחיל עונש עומס ריבועי; מעל 1.0 תעבורה נזרקת.' } },
  { term: 'PDR / PLR', code: 'metrics.MetricsTracker',
    text: { en: 'Packet delivery ratio = delivered demand ÷ offered demand. Packet loss ratio = 1 − PDR.', he: 'יחס מסירה = ביקוש שהגיע ÷ ביקוש שנשלח. יחס אובדן = 1 − PDR.' } },
  { term: 'Held-out seeds', code: 'evaluation.eval_seeds()',
    text: { en: 'Evaluation traffic comes from seeds the agent never trained on, so the score cannot be memorised.', he: 'תעבורת ההערכה מגיעה מ-seeds שהסוכן לא התאמן עליהם, כך שאי אפשר לשנן את הציון.' } },
]

export interface Phase {
  title: Localized
  items: string[]
  checkpoint: Localized
  critical?: Localized
}

export const phases: Phase[] = [
  { title: { en: 'Foundations', he: 'יסודות' }, items: ['config.py', 'topology.py', 'traffic.py'],
    checkpoint: { en: 'Both topologies build and every invalid input raises ValueError.', he: 'שתי הטופולוגיות נבנות וכל קלט לא תקין זורק ValueError.' } },
  { title: { en: 'Environment & baselines', he: 'סביבה ו-baselines' }, items: ['environment.py', 'metrics.py', 'baselines.py'],
    checkpoint: { en: 'Shortest path and congestion-aware route every flow with zero failures.', he: 'Shortest path ו-congestion-aware מנתבים כל זרימה בלי כשלים.' } },
  { title: { en: 'Learning', he: 'למידה' }, items: ['agent.py', 'training.py', 'evaluation.py'],
    checkpoint: { en: 'Zero agent failures, and the agent matches or beats the baselines.', he: 'אפס כשלים לסוכן, והסוכן משתווה ל-baselines או עוקף אותם.' },
    critical: { en: 'Not in the original plan: reward calibration and the loop fixes (issues #13–#15). Always reserve time for this in RL work.', he: 'לא היה בתוכנית המקורית: כיול ה-reward ותיקוני הלולאות (תקלות #13–#15). בעבודת RL תמיד לשריין לזה זמן.' } },
  { title: { en: 'Experiments & docs', he: 'ניסויים ותיעוד' }, items: ['experiments.py', 'plotting.py', 'cli.py', 'tests', 'docs', 'web'],
    checkpoint: { en: '10-seed benchmark with significance tests and a load sweep, all tests green, ruff clean, live site on GitHub Pages.', he: 'ניסוי 10 seeds עם מבחני מובהקות וסריקת עומס, כל הבדיקות ירוקות, ruff נקי, אתר חי ב-GitHub Pages.' } },
]

export interface Decision {
  id: string
  title: Localized
  decision: Localized
  why: Localized
  cost: Localized
}

export const decisions: Decision[] = [
  { id: 'ADR-1', title: { en: 'A table, not a neural network', he: 'טבלה ולא רשת נוירונים' },
    decision: { en: 'Tabular Q-learning with a Python dict.', he: 'Q-learning טבלאי עם dict של Python.' },
    why: { en: '432 states × ≤4 actions: exact, inspectable values with no approximation error or replay buffer.', he: '432 מצבים × עד 4 פעולות: ערכים מדויקים וניתנים לבדיקה, בלי שגיאת קירוב ובלי replay buffer.' },
    cost: { en: 'Does not scale to rich states (per-link load would be 3³⁰ states).', he: 'לא מתרחב ל-state עשיר (עומס לכל קישור = 3³⁰ מצבים).' } },
  { id: 'ADR-2', title: { en: 'Local state only', he: 'state מקומי בלבד' },
    decision: { en: '(current, destination, mean outgoing-load bin).', he: '(נוכחי, יעד, דרגת העומס היוצא הממוצע).' },
    why: { en: 'A real router knows its own interface counters; global state arrives late.', he: 'נתב אמיתי מכיר את מוני הממשקים שלו; מידע גלובלי מגיע באיחור.' },
    cost: { en: 'A mean hides which link is hot, and the flow size is invisible.', he: 'ממוצע מסתיר איזה קישור עמוס, וגודל הזרימה לא נראה.' } },
  { id: 'ADR-3', title: { en: 'Flow-level simulation', he: 'סימולציה ברמת זרימות' },
    decision: { en: 'Route each flow hop by hop; loads decay ×0.85 between flows.', he: 'כל זרימה מנותבת hop אחר hop; עומסים דועכים פי 0.85 בין זרימות.' },
    why: { en: 'The research question is about routing decisions, not TCP dynamics.', he: 'שאלת המחקר עוסקת בהחלטות ניתוב, לא בדינמיקה של TCP.' },
    cost: { en: 'No real queues; M/M/1 appears only as the motivation for the penalty shape.', he: 'אין תורים אמיתיים; M/M/1 מופיע רק כהצדקה לצורת העונש.' } },
  { id: 'ADR-4', title: { en: 'The agent does not know the environment', he: 'הסוכן לא מכיר את הסביבה' },
    decision: { en: 'QLearningAgent sees only hashable states and integer actions.', he: 'QLearningAgent רואה רק states שניתנים ל-hash ופעולות מספריות.' },
    why: { en: 'Testable in isolation, swappable, and no circular imports.', he: 'נבדק בבידוד, ניתן להחלפה, ואין ייבוא מעגלי.' },
    cost: { en: 'An adapter is needed to plug it into the policy loop.', he: 'צריך adapter כדי לחבר אותו ללולאת המדיניות.' } },
  { id: 'ADR-5', title: { en: 'Enforced train/eval split', he: 'הפרדה אכופה בין אימון להערכה' },
    decision: { en: 'update() raises in eval mode; evaluation seeds are offset by 10⁶.', he: 'update() זורק שגיאה במצב הערכה; seeds ההערכה מוזזים ב-10⁶.' },
    why: { en: 'A convention is not a guarantee. The code makes leakage impossible.', he: 'מוסכמה היא לא הבטחה. הקוד הופך דליפה לבלתי אפשרית.' },
    cost: { en: 'Slightly more code in the evaluation path.', he: 'קצת יותר קוד במסלול ההערכה.' } },
  { id: 'ADR-6', title: { en: 'Loop masking + dead-end termination', he: 'חסימת לולאות + סיום במבוי סתום' },
    decision: { en: 'Visited neighbours are not offered; entering a dead end ends the flow at once.', he: 'שכנים שבוקרו לא מוצעים; כניסה למבוי סתום מסיימת את הזרימה מיד.' },
    why: { en: 'Fixes state aliasing and puts the penalty on the decision that caused it.', he: 'מתקן state aliasing ושם את העונש על ההחלטה שגרמה לו.' },
    cost: { en: 'The action set now depends on the path, not only on the state tuple.', he: 'קבוצת הפעולות תלויה עכשיו במסלול, לא רק ב-state.' } },
]

export interface QuizItem {
  q: Localized
  a: Localized
}

export const quiz: QuizItem[] = [
  { q: { en: 'Why does the state contain only local load and not the load of the whole network?', he: 'למה ה-state מכיל רק עומס מקומי ולא את העומס של כל הרשת?' },
    a: { en: 'A router realistically knows only its own interfaces, and a small local state keeps the table learnable (432 states). Matching a global-state baseline with it is the interesting result.', he: 'נתב יודע באופן מציאותי רק על הממשקים שלו, ו-state מקומי קטן משאיר את הטבלה ניתנת ללמידה (432 מצבים). להשתוות בעזרתו ל-baseline עם מידע גלובלי זו התוצאה המעניינת.' } },
  { q: { en: 'What would go wrong if max Q(s′,a′) were not zeroed on terminal steps?', he: 'מה ישתבש אם לא נאפס את max Q(s′,a′) בצעד סופי?' },
    a: { en: 'The agent would add value from a "future" that does not exist, for example the next flow’s state, and leak credit across unrelated flows.', he: 'הסוכן היה מוסיף ערך מ"עתיד" שלא קיים, למשל המצב של הזרימה הבאה, ומעביר קרדיט בין זרימות שלא קשורות.' } },
  { q: { en: 'Why is initialising the Q-table to 0 "optimistic" here?', he: 'למה אתחול ה-Q-table לאפס הוא "אופטימי" כאן?' },
    a: { en: 'Every hop reward is negative, so an untried action (Q = 0) looks better than a tried one. That alone drives exploration.', he: 'כל תגמול hop שלילי, ולכן פעולה שלא נוסתה (Q = 0) נראית טובה יותר מפעולה שנוסתה. זה לבד מניע חקירה.' } },
  { q: { en: 'What is reward hacking and how did it show up here?', he: 'מה זה reward hacking ואיך זה הופיע כאן?' },
    a: { en: 'The agent optimises the reward literally. With a −50 loop penalty, failing was cheaper than delivering through congestion, so it looped on purpose. All failures became −100.', he: 'הסוכן ממקסם את ה-reward כפשוטו. עם עונש לולאה של ‎−50, להיכשל היה זול יותר מלמסור דרך עומס, אז הוא יצר לולאות בכוונה. כל הכשלים הפכו ל-‎−100.' } },
  { q: { en: 'How do you make sure the evaluation does not cheat?', he: 'איך מוודאים שההערכה לא מרמה?' },
    a: { en: 'Disjoint seed ranges for training and evaluation, a locked agent (update raises), and the same episodes for every policy.', he: 'טווחי seeds נפרדים לאימון ולהערכה, סוכן נעול (update זורק שגיאה), ואותם פרקים לכל מדיניות.' } },
]

export interface Exercise {
  level: 1 | 2 | 3 | 4
  title: Localized
  text: Localized
}

export const exercises: Exercise[] = [
  { level: 1, title: { en: 'Turn the knobs', he: 'לשחק עם הפרמטרים' },
    text: { en: 'Copy configs/default.yaml and try profile: moderate, epsilon_decay: 0.99, gamma: 0.5 or loop_penalty: −50. Predict the effect before you run it.', he: 'להעתיק את configs/default.yaml ולנסות profile: moderate, ‏epsilon_decay: 0.99, ‏gamma: 0.5 או loop_penalty: ‎−50. לנחש את ההשפעה לפני ההרצה.' } },
  { level: 2, title: { en: 'Add a topology', he: 'להוסיף טופולוגיה' },
    text: { en: 'Add ring_8 (8 nodes in a ring with two shortcuts) to topology.py, with a test that it is strongly connected.', he: 'להוסיף ring_8 (טבעת של 8 צמתים עם שני קיצורים) ל-topology.py, עם בדיקה שהיא strongly connected.' } },
  { level: 2, title: { en: 'A new metric', he: 'מדד חדש' },
    text: { en: 'Measure the share of delivered flows that used the minimum-latency path. Where should it live, and why not in metrics.py?', he: 'למדוד איזה חלק מהזרימות שנמסרו עברו בנתיב בעל ההשהיה המינימלית. איפה המדד צריך לשבת, ולמה לא ב-metrics.py?' } },
  { level: 3, title: { en: 'Double Q-learning', he: 'Double Q-learning' },
    text: { en: 'Use two tables to reduce overestimation bias, and test one update by hand like test_exact_bellman_update.', he: 'להשתמש בשתי טבלאות כדי להקטין overestimation bias, ולבדוק עדכון אחד ידנית כמו test_exact_bellman_update.' } },
  { level: 3, title: { en: 'Safe fallback', he: 'Fallback בטוח' },
    text: { en: 'In a state never seen in training, fall back to shortest path instead of the lowest node id. Count how often it happens.', he: 'במצב שלא נראה באימון, ליפול ל-shortest path במקום ל-id הנמוך. לספור כמה פעמים זה קורה.' } },
  { level: 4, title: { en: 'Significance and load sweep', he: 'מובהקות וסריקת עומס' },
    text: { en: 'Run 10 seeds with a paired t-test, then sweep capacity_scale from 1.5 to 0.6 and plot where learning starts to pay off.', he: 'להריץ 10 seeds עם paired t-test, ואז לסרוק את capacity_scale מ-1.5 עד 0.6 ולצייר איפה הלמידה מתחילה להשתלם.' } },
]
