const SUGGESTIONS = [
  'Хочу комедию на вечер',
  'Что-нибудь как Интерстеллар',
  'Триллер, но без ужасов',
]

export default function WelcomeScreen({ onSuggestionClick }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-8 px-4">
      <div className="text-center space-y-3">
        <h1 className="font-display text-3xl sm:text-4xl text-ink">
          Что посмотреть?
        </h1>
        <p className="text-sm text-muted max-w-sm mx-auto leading-relaxed">
          Опишите настроение, жанр или фильм, который вам нравится,
          и я подберу что-то подходящее
        </p>
      </div>

      <div className="flex flex-wrap justify-center gap-2">
        {SUGGESTIONS.map(text => (
          <button
            key={text}
            onClick={() => onSuggestionClick(text)}
            className="px-4 py-2 text-sm text-muted bg-surface rounded-lg
                       hover:text-ink hover:bg-elevated
                       focus-visible:outline-2 focus-visible:outline-amber focus-visible:outline-offset-2
                       transition-colors duration-150"
          >
            {text}
          </button>
        ))}
      </div>
    </div>
  )
}
