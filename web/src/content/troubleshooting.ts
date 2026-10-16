import type { Localized } from './localized'

export type IssueCategory = 'setup' | 'quality' | 'learning' | 'experiments'

export interface Issue {
  id: number
  category: IssueCategory
  /** True when the issue actually happened while building the project. */
  real?: boolean
  title: Localized
  symptom: Localized
  cause: Localized
  fix: Localized[]
  lesson?: Localized
  code?: string
}

export const issues: Issue[] = [
  {
    id: 1, category: 'setup', real: true,
    title: { en: "ModuleNotFoundError: No module named 'numpy'", he: "ModuleNotFoundError: No module named 'numpy'" },
    symptom: { en: 'Importing numpy fails although you installed it.', he: 'ייבוא numpy נכשל למרות שהתקנת אותו.' },
    cause: { en: "You ran the system Python, not the project's virtual environment.", he: 'הרצת את ה-Python של המערכת ולא את הסביבה הווירטואלית של הפרויקט.' },
    fix: [
      { en: 'Check with `which python`: the path should be inside .venv.', he: 'לבדוק עם `which python`: הנתיב צריך להיות בתוך .venv.' },
      { en: 'Run `source .venv/bin/activate`, or call `.venv/bin/python` directly (the Makefile already does).', he: 'להריץ `source .venv/bin/activate`, או לקרוא ישירות ל-`.venv/bin/python` (ה-Makefile כבר עושה את זה).' },
    ],
    lesson: { en: 'One virtual environment per project. Never pip install into the global Python.', he: 'סביבה וירטואלית אחת לכל פרויקט. אף פעם לא pip install ל-Python הגלובלי.' },
  },
  {
    id: 2, category: 'setup',
    title: { en: "No module named 'meshmind'", he: "No module named 'meshmind'" },
    symptom: { en: '`python -m meshmind.cli` fails from the project folder.', he: '`python -m meshmind.cli` נכשל מתיקיית הפרויקט.' },
    cause: { en: 'The code lives in src/ (src layout), which Python does not search by default.', he: 'הקוד נמצא ב-src/ (src layout), ו-Python לא מחפש שם כברירת מחדל.' },
    fix: [{ en: 'Install in editable mode: `pip install -e ".[dev]"` (or `make install`).', he: 'להתקין במצב editable: `pip install -e ".[dev]"` (או `make install`).' }],
    lesson: { en: 'The src layout forces a real install, so tests never pass just because of the current directory.', he: 'ה-src layout מכריח התקנה אמיתית, כך שבדיקות לא עוברות רק בזכות התיקייה הנוכחית.' },
    code: 'pyproject.toml',
  },
  {
    id: 3, category: 'setup',
    title: { en: 'zip() takes no keyword arguments / no itertools.pairwise', he: 'zip() takes no keyword arguments / אין itertools.pairwise' },
    symptom: { en: 'A TypeError or AttributeError as soon as the code runs.', he: 'TypeError או AttributeError מיד כשהקוד רץ.' },
    cause: { en: 'An old Python. The code uses zip(strict=...) and itertools.pairwise from Python 3.10.', he: 'גרסת Python ישנה. הקוד משתמש ב-zip(strict=...) וב-itertools.pairwise מ-Python 3.10.' },
    fix: [{ en: 'Use Python 3.11 or newer (the project pins 3.12 in .python-version).', he: 'להשתמש ב-Python 3.11 ומעלה (הפרויקט מגדיר 3.12 ב-.python-version).' }],
    code: '.python-version',
  },
  {
    id: 4, category: 'setup', real: true,
    title: { en: 'The first matplotlib run seems stuck', he: 'ההרצה הראשונה של matplotlib נראית תקועה' },
    symptom: { en: '"Matplotlib is building the font cache; this may take a moment."', he: '"Matplotlib is building the font cache; this may take a moment."' },
    cause: { en: 'On first use matplotlib scans the fonts installed on the machine.', he: 'בשימוש הראשון matplotlib סורק את הפונטים שמותקנים במחשב.' },
    fix: [{ en: 'Wait. It happens once only.', he: 'לחכות. זה קורה פעם אחת בלבד.' }],
  },
  {
    id: 5, category: 'setup', real: true,
    title: { en: '`code` command not found (opening VS Code)', he: 'הפקודה `code` לא נמצאה (פתיחת VS Code)' },
    symptom: { en: 'zsh: command not found: code', he: 'zsh: command not found: code' },
    cause: { en: "VS Code's shell command is not installed in PATH.", he: 'פקודת ה-shell של VS Code לא מותקנת ב-PATH.' },
    fix: [
      { en: 'Right now: `open -a "Visual Studio Code" .`', he: 'מיידית: `open -a "Visual Studio Code" .`' },
      { en: "Permanently: in VS Code press Cmd+Shift+P and run \"Shell Command: Install 'code' command in PATH\".", he: "לתמיד: ב-VS Code ללחוץ Cmd+Shift+P ולהריץ \"Shell Command: Install 'code' command in PATH\"." },
    ],
  },
  {
    id: 6, category: 'quality',
    title: { en: 'pytest cannot import the package', he: 'pytest לא מצליח לייבא את החבילה' },
    symptom: { en: 'ImportError while collecting tests.', he: 'ImportError בזמן איסוף הבדיקות.' },
    cause: { en: 'pytest was started from another folder, or the package is not installed.', he: 'pytest הופעל מתיקייה אחרת, או שהחבילה לא מותקנת.' },
    fix: [{ en: 'Run pytest from the project root. pyproject.toml sets `pythonpath = ["src"]` for pytest.', he: 'להריץ pytest מתיקיית השורש. ה-pyproject.toml מגדיר `pythonpath = ["src"]` ל-pytest.' }],
    code: 'pyproject.toml',
  },
  {
    id: 7, category: 'quality', real: true,
    title: { en: 'ruff: RUF007 Prefer itertools.pairwise()', he: 'ruff: RUF007 Prefer itertools.pairwise()' },
    symptom: { en: '`ruff check` fails on `zip(nodes, nodes[1:])`.', he: '`ruff check` נכשל על `zip(nodes, nodes[1:])`.' },
    cause: { en: 'ruff recognises the "consecutive pairs" pattern, which has a dedicated function.', he: 'ruff מזהה את דפוס "זוגות עוקבים", שיש לו פונקציה ייעודית.' },
    fix: [
      { en: 'Use `itertools.pairwise(nodes)`.', he: 'להשתמש ב-`itertools.pairwise(nodes)`.' },
      { en: 'After `ruff check --fix --unsafe-fixes`, always review the diff.', he: 'אחרי `ruff check --fix --unsafe-fixes`, תמיד לבדוק את ה-diff.' },
    ],
    lesson: { en: 'A linter teaches the idioms of the language, not only style.', he: 'linter מלמד את ה-idioms של השפה, לא רק סגנון.' },
    code: 'src/meshmind/topology.py',
  },
  {
    id: 8, category: 'quality',
    title: { en: '`ruff format --check` fails after a manual edit', he: '`ruff format --check` נכשל אחרי עריכה ידנית' },
    symptom: { en: 'CI or `make lint` reports files that would be reformatted.', he: 'CI או `make lint` מדווחים על קבצים שיעוצבו מחדש.' },
    cause: { en: 'The edit does not match the formatter style.', he: 'העריכה לא תואמת לסגנון ה-formatter.' },
    fix: [
      { en: 'Run `make format` (ruff format, then ruff check --fix).', he: 'להריץ `make format` (ruff format ואחריו ruff check --fix).' },
      { en: 'Install the Ruff extension in VS Code and turn on Format on Save.', he: 'להתקין את תוסף Ruff ב-VS Code ולהפעיל Format on Save.' },
    ],
  },
  {
    id: 9, category: 'quality',
    title: { en: 'A test passes sometimes and fails sometimes (flaky)', he: 'בדיקה שעוברת לפעמים ונכשלת לפעמים (flaky)' },
    symptom: { en: 'The same test gives different results on different runs.', he: 'אותה בדיקה נותנת תוצאות שונות בהרצות שונות.' },
    cause: { en: 'Randomness that does not come from a seed: the global np.random, Python random, or set ordering.', he: 'אקראיות שלא מגיעה מ-seed: np.random הגלובלי, random של Python, או סדר של set.' },
    fix: [
      { en: 'Give every component its own `np.random.default_rng(seed)`.', he: 'לתת לכל רכיב `np.random.default_rng(seed)` משלו.' },
      { en: 'Break ties deterministically (lowest node id) and return sorted neighbour lists.', he: 'לשבור שוויון באופן דטרמיניסטי (ה-id הנמוך) ולהחזיר רשימות שכנים ממוינות.' },
    ],
    code: 'tests/test_training.py',
  },
  {
    id: 10, category: 'learning',
    title: { en: 'The reward does not improve during training', he: 'ה-reward לא משתפר במהלך האימון' },
    symptom: { en: 'The reward curve stays flat.', he: 'עקומת ה-reward נשארת שטוחה.' },
    cause: { en: 'ε decays too slowly (still exploring) or too fast (never explored), or update() is never called.', he: 'ε יורד לאט מדי (עדיין חוקר) או מהר מדי (לא חקר בכלל), או ש-update() לא נקרא.' },
    fix: [
      { en: 'Check the epsilon and q_table_size columns in training_history.csv.', he: 'לבדוק את העמודות epsilon ו-q_table_size ב-training_history.csv.' },
      { en: 'ε reaches its floor after ln(ε_end/ε_start) / ln(decay) episodes: about 1,497 with 0.998, half of the 3,000.', he: 'ε מגיע לרצפה אחרי ln(ε_end/ε_start) / ln(decay) פרקים: כ-1,497 עם 0.998, חצי מ-3,000.' },
    ],
    code: 'configs/default.yaml',
  },
  {
    id: 11, category: 'learning',
    title: { en: 'The TD error does not go down to zero', he: 'ה-TD error לא יורד לאפס' },
    symptom: { en: 'mean_abs_td_error falls and then levels off.', he: 'mean_abs_td_error יורד ואז מתייצב.' },
    cause: { en: 'α is constant and link loads keep changing (a non-stationary environment), so the error cannot vanish.', he: 'α קבוע ועומסי הקישורים משתנים כל הזמן (סביבה לא סטציונרית), ולכן השגיאה לא יכולה להיעלם.' },
    fix: [{ en: 'Expected behaviour. The test only requires the last 10% of episodes to be clearly lower than the first 10%.', he: 'התנהגות צפויה. הבדיקה רק דורשת ש-10% הפרקים האחרונים יהיו נמוכים בבירור מ-10% הראשונים.' }],
    code: 'tests/test_training.py',
  },
  {
    id: 12, category: 'learning',
    title: { en: 'Failures with reason invalid_action', he: 'כשלים עם הסיבה invalid_action' },
    symptom: { en: 'failure_breakdown() returns {"invalid_action": N}.', he: 'failure_breakdown() מחזיר {"invalid_action": N}.' },
    cause: { en: 'The policy chose a node that is not an outgoing neighbour.', he: 'המדיניות בחרה צומת שאינו שכן יוצא.' },
    fix: [{ en: 'Policies must choose only from get_valid_actions(). The environment protects itself: −100 and no load change.', he: 'מדיניות חייבת לבחור רק מתוך get_valid_actions(). הסביבה מגינה על עצמה: ‎−100 ובלי שינוי עומס.' }],
    code: 'src/meshmind/environment.py',
  },
  {
    id: 13, category: 'learning', real: true,
    title: { en: 'The agent fails with loops even after long training', he: 'הסוכן נכשל בלולאות גם אחרי אימון ארוך' },
    symptom: { en: '131–166 of 2,500 evaluation flows failed, all as loops. Training longer did not help.', he: '131–166 מתוך 2,500 זרימות בהערכה נכשלו, כולן בלולאה. אימון ארוך יותר לא עזר.' },
    cause: { en: 'State aliasing: (current, destination, bin) does not remember where the flow came from. "From B go to A" is right when the flow started at B and a loop when it just came from A.', he: 'State aliasing: ‏(נוכחי, יעד, bin) לא זוכר מאיפה הזרימה הגיעה. "מ-B לך ל-A" נכון כשהזרימה התחילה ב-B, ולולאה כשהיא הרגע הגיעה מ-A.' },
    fix: [{ en: 'Loop masking: get_valid_actions() removes neighbours already on the flow’s path.', he: 'Loop masking: ‏get_valid_actions() מסיר שכנים שכבר נמצאים במסלול הזרימה.' }],
    lesson: { en: 'When the state is not Markov, more training will not help. Change the state or the action space.', he: 'כשה-state לא מרקובי, אימון נוסף לא יעזור. צריך לשנות את ה-state או את מרחב הפעולות.' },
    code: 'src/meshmind/environment.py',
  },
  {
    id: 14, category: 'learning', real: true,
    title: { en: 'Loops through the Atlanta-M5 leaf node', he: 'לולאות דרך צומת העלה Atlanta-M5' },
    symptom: { en: 'Failed paths kept repeating the same pattern: 7 → 11 → 7.', he: 'המסלולים שנכשלו חזרו על אותו דפוס: 7 → 11 → 7.' },
    cause: { en: 'The penalty landed one step too late, on the leaf’s state. That same state-action is the right move when a flow starts at the leaf, so on average the detour looked fine.', he: 'העונש נחת צעד אחד מאוחר מדי, על המצב של העלה. אותו זוג מצב-פעולה הוא הצעד הנכון כשזרימה מתחילה בעלה, כך שבממוצע העקיפה נראתה סבירה.' },
    fix: [{ en: 'Entering a node whose neighbours are all visited ends the flow immediately (_is_dead_end), so the penalty hits the decision that caused it. Failures: 150 → 19.', he: 'כניסה לצומת שכל שכניו כבר בוקרו מסיימת את הזרימה מיד (_is_dead_end), כך שהעונש פוגע בהחלטה שגרמה לו. כשלים: 150 → 19.' }],
    lesson: { en: 'Credit assignment: punish the decision that caused the problem, not its unavoidable consequence.', he: 'Credit assignment: להעניש את ההחלטה שגרמה לבעיה, לא את התוצאה הבלתי נמנעת שלה.' },
    code: 'src/meshmind/environment.py',
  },
  {
    id: 15, category: 'learning', real: true,
    title: { en: 'The agent loops traffic on purpose (reward hacking)', he: 'הסוכן מסובב תעבורה בלולאה בכוונה (reward hacking)' },
    symptom: { en: 'Under high load: 375 loop failures, more than under low load.', he: 'בעומס גבוה: 375 כשלי לולאה, יותר מאשר בעומס נמוך.' },
    cause: { en: 'The loop penalty was −50, while delivering through congested links could cost more (penalty latency up to 12.25× plus a drop penalty up to −50). For the agent, failing paid off.', he: 'עונש הלולאה היה ‎−50, ומסירה דרך קישורים עמוסים יכלה לעלות יותר (השהיית עונש עד פי 12.25 ועוד עונש drop עד ‎−50). בשביל הסוכן, להיכשל השתלם.' },
    fix: [
      { en: 'Weight latency by 0.1 per ms.', he: 'לתת ל-latency משקל של 0.1 לכל ms.' },
      { en: 'Set every failure to −100, below the worst feasible delivery (about −76). Failures: 375 → 0.', he: 'לקבוע כל כישלון ל-‎−100, מתחת למסירה הגרועה ביותר האפשרית (בערך ‎−76). כשלים: 375 → 0.' },
    ],
    lesson: { en: "The reward must encode the operator's order of preference. The agent does what is rewarded, not what you meant.", he: 'ה-reward חייב לקודד את סדר העדיפויות של המפעיל. הסוכן עושה את מה שמתוגמל, לא את מה שהתכוונת.' },
    code: 'configs/default.yaml',
  },
  {
    id: 16, category: 'learning',
    title: { en: 'The Q-table changes during evaluation', he: 'ה-Q-table משתנה בזמן ההערכה' },
    symptom: { en: 'Evaluation scores drift between runs, or improve the more you evaluate.', he: 'ציוני ההערכה משתנים בין הרצות, או משתפרים ככל שמעריכים יותר.' },
    cause: { en: 'update() was called inside the evaluation loop, or exploration was left on.', he: 'update() נקרא בתוך לולאת ההערכה, או שהחקירה נשארה פעילה.' },
    fix: [{ en: 'evaluate_agent switches eval_mode on (ε = 0), and update() raises RuntimeError in eval mode. A test deep-copies the table and compares.', he: 'evaluate_agent מפעיל eval_mode ‏(ε = 0), ו-update() זורק RuntimeError במצב הזה. בדיקה עושה deepcopy לטבלה ומשווה.' }],
    code: 'src/meshmind/evaluation.py',
  },
  {
    id: 17, category: 'experiments',
    title: { en: 'Every policy except random scores almost the same', he: 'כל המדיניות חוץ מ-random מקבלות כמעט אותו ציון' },
    symptom: { en: 'Under the moderate profile all PDRs are about 0.99.', he: 'בפרופיל moderate כל ה-PDR בסביבות 0.99.' },
    cause: { en: 'Without congestion the shortest path is already the best path. There is nothing to improve.', he: 'בלי עומס, הנתיב הקצר הוא כבר הנתיב הטוב ביותר. אין מה לשפר.' },
    fix: [{ en: 'Not a bug, a result. The default profile is high, where routing choices matter. Report it honestly.', he: 'לא באג, תוצאה. ברירת המחדל היא high, שם להחלטות הניתוב יש משמעות. לדווח על זה בכנות.' }],
  },
  {
    id: 18, category: 'experiments',
    title: { en: 'std = 0.000 in the table', he: 'std = 0.000 בטבלה' },
    symptom: { en: 'Every ± value is zero.', he: 'כל ערכי ה-± הם אפס.' },
    cause: { en: 'Only one seed ran. The sample std (ddof=1) is undefined for n = 1, so 0 is reported.', he: 'רץ רק seed אחד. סטיית התקן המדגמית (ddof=1) לא מוגדרת עבור n = 1, ולכן מדווח 0.' },
    fix: [{ en: 'Use at least 3 seeds. The CLI table hides ± when there is a single seed.', he: 'להשתמש בלפחות 3 seeds. טבלת ה-CLI מסתירה את ה-± כשיש seed יחיד.' }],
    code: 'src/meshmind/metrics.py',
  },
  {
    id: 19, category: 'experiments',
    title: { en: 'FileNotFoundError: run experiments first', he: 'FileNotFoundError: run experiments first' },
    symptom: { en: '`meshmind plot` stops with an error.', he: '`meshmind plot` נעצר עם שגיאה.' },
    cause: { en: 'summary.json and training_history.csv do not exist yet in the results folder.', he: 'summary.json ו-training_history.csv עדיין לא קיימים בתיקיית התוצאות.' },
    fix: [{ en: 'Run `make experiments` first (it draws the figures too), or pass the right --results-dir.', he: 'להריץ קודם `make experiments` (הוא גם מצייר את הגרפים), או להעביר את --results-dir הנכון.' }],
    code: 'src/meshmind/plotting.py',
  },
  {
    id: 20, category: 'experiments',
    title: { en: '"Too good to be true": suspected data leakage', he: '"טוב מכדי להיות אמיתי": חשד לדליפת נתונים' },
    symptom: { en: 'The agent scores suspiciously well.', he: 'הסוכן מקבל ציון טוב באופן חשוד.' },
    cause: { en: 'It may be evaluated on the same traffic it trained on.', he: 'ייתכן שהוא נבחן על אותה תעבורה שהתאמן עליה.' },
    fix: [
      { en: 'Training uses seeds s … s+2999 and evaluation s+10⁶ …: the ranges never overlap (test_eval_scenarios_are_held_out).', he: 'האימון משתמש ב-seeds s … s+2999 וההערכה ב-s+10⁶ …: הטווחים לא חופפים (test_eval_scenarios_are_held_out).' },
      { en: 'All four policies are scored on the same 100 episodes (a paired comparison).', he: 'כל ארבע המדיניות נבחנות על אותם 100 פרקים (השוואה מזווגת).' },
    ],
    code: 'tests/test_evaluation.py',
  },
]
