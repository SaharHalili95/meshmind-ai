import type { Localized } from './localized'

export interface SummarySection {
  id: string
  icon: string
  title: Localized
  /** Technology names, always shown left-to-right next to the title. */
  tech?: string
  items: Localized[]
}

/** Plain summary of what the project contains, shown on the "About this project" page. */
export const summarySections: SummarySection[] = [
  {
    id: 'research',
    icon: 'pi pi-search',
    title: { en: 'Research', he: 'מחקר' },
    tech: 'Q-learning · Abilene',
    items: [
      { en: 'Question: can an agent that sees only local congestion match a router that sees the whole network?', he: 'השאלה: האם סוכן שרואה רק עומס מקומי יכול להשתוות לנתב שרואה את כל הרשת?' },
      { en: '10 seeds, disjoint train and evaluation traffic, all policies scored on identical episodes, exact permutation tests with bootstrap CIs.', he: '10 seeds, תעבורת אימון והערכה נפרדות, כל המדיניות נבחנות על אותם פרקים בדיוק, ומבחני פרמוטציות מדויקים עם רווחי סמך bootstrap.' },
      { en: 'Result: significantly more traffic delivered than shortest path (+1.8 pts, 10/10 seeds, p = 0.002), and a significant win over the global congestion-aware router on delivery, latency and link utilization (8.8% less). A load sweep shows a crossover: below load 0.9 the global router is slightly better.', he: 'התוצאה: יותר תעבורה באופן מובהק מאשר ב-shortest path ‏(‎+1.8 נק׳, 10/10 seeds, ‏p = 0.002), וניצחון מובהק על הנתב הגלובלי congestion-aware במסירה, בהשהיה ובניצולת הקישורים (8.8% פחות). סריקת עומס מראה נקודת מעבר: מתחת לעומס 0.9 הנתב הגלובלי טוב במעט.' },
      { en: 'Three real failures diagnosed and fixed: state aliasing, late credit assignment, and reward hacking.', he: 'שלוש תקלות אמיתיות אובחנו ותוקנו: state aliasing, credit assignment מאוחר ו-reward hacking.' },
    ],
  },
  {
    id: 'python',
    icon: 'pi pi-server',
    title: { en: 'Simulator and agent', he: 'סימולטור וסוכן' },
    tech: 'Python · NetworkX · NumPy',
    items: [
      { en: 'Network model with capacity, propagation latency, a quadratic congestion penalty above 80% and proportional packet loss.', he: 'מודל רשת עם קיבולת, השהיית התפשטות, עונש עומס ריבועי מעל 80% ואובדן חבילות יחסי.' },
      { en: 'Gym-style environment: reset, get_observation, get_valid_actions, step.', he: 'סביבה בסגנון Gym: ‏reset, ‏get_observation, ‏get_valid_actions, ‏step.' },
      { en: 'Q-learning from first principles: exact Bellman update, no bootstrapping on terminal steps, ε-greedy with decay.', he: 'Q-learning מעקרונות ראשונים: עדכון Bellman מדויק, בלי bootstrap בצעד סופי, ε-greedy עם דעיכה.' },
      { en: 'Multi-seed pipeline, Matplotlib figures and a CLI with five commands.', he: 'צינור ניסויים רב-seed, גרפי Matplotlib ו-CLI עם חמש פקודות.' },
    ],
  },
  {
    id: 'quality',
    icon: 'pi pi-check-square',
    title: { en: 'Quality', he: 'איכות' },
    tech: 'pytest · ruff · Vitest',
    items: [
      { en: '130 pytest tests that check exact numbers: hand-computed Bellman updates, the penalty formula, PDR edge cases, hand-enumerated permutation p-values.', he: '130 בדיקות pytest שבודקות מספרים מדויקים: עדכוני Bellman שחושבו ידנית, נוסחת העונש, מקרי קצה של PDR, ו-p-values של מבחן פרמוטציות שנספרו ידנית.' },
      { en: 'Every source of randomness is seeded, so every result regenerates bit for bit.', he: 'כל מקור אקראיות מקבל seed, כך שכל תוצאה משתחזרת ביט אחר ביט.' },
      { en: 'Type hints everywhere, typed and validated configuration, ruff check and format clean.', he: 'Type hints בכל מקום, הגדרות עם טיפוסים ואימות, ruff check ו-format נקיים.' },
      { en: 'CI on GitHub Actions runs the Python tests, lint, and the website type-check, tests and build.', he: 'CI ב-GitHub Actions מריץ את בדיקות ה-Python, lint, ואת בדיקות הטיפוסים, הבדיקות והבנייה של האתר.' },
    ],
  },
  {
    id: 'web',
    icon: 'pi pi-desktop',
    title: { en: 'This website', he: 'האתר הזה' },
    tech: 'Vue 3 · TypeScript · PrimeVue',
    items: [
      { en: 'A TypeScript port of the simulator and agent: train and watch the agent route traffic, right in the browser.', he: 'פורט של הסימולטור והסוכן ל-TypeScript: מאמנים וצופים בסוכן מנתב תעבורה, ישירות בדפדפן.' },
      { en: 'Benchmark tables and charts generated from the real Python result files.', he: 'טבלאות וגרפים של הניסוי, שנוצרים מקבצי התוצאות האמיתיים של ה-Python.' },
      { en: 'Interactive architecture walkthrough, a learning hub and a searchable troubleshooting guide.', he: 'סיור אינטראקטיבי בארכיטקטורה, אזור למידה ומדריך תקלות עם חיפוש.' },
      { en: 'English and Hebrew with full right-to-left layout, and light and dark themes.', he: 'עברית ואנגלית עם תמיכה מלאה מימין לשמאל, וערכות צבעים בהירה וכהה.' },
    ],
  },
]
