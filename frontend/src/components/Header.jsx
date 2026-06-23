export default function Header({ onHomeClick, showHome }) {
  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-surface">
      <button
        onClick={onHomeClick}
        className="font-display text-lg text-ink hover:text-amber transition-colors duration-150
                   focus-visible:outline-2 focus-visible:outline-amber focus-visible:outline-offset-2"
      >
        Hybrid Movie Recommender
      </button>
      {showHome && (
        <button
          onClick={onHomeClick}
          className="flex items-center gap-1.5 text-sm text-muted hover:text-ink
                     transition-colors duration-150
                     focus-visible:outline-2 focus-visible:outline-amber focus-visible:outline-offset-2"
          aria-label="На главную"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 12l9-9 9 9" />
            <path d="M9 21V9h6v12" />
          </svg>
          На главную
        </button>
      )}
    </header>
  )
}
