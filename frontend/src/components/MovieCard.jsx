export default function MovieCard({ movie }) {
  const year = movie.release_date?.slice(0, 4)

  return (
    <a
      href={movie.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex-shrink-0 w-56 rounded-lg bg-surface overflow-hidden
                 transition-colors duration-200 hover:bg-elevated
                 focus-visible:outline-2 focus-visible:outline-amber focus-visible:outline-offset-2"
    >
      <div className="aspect-[2/3] bg-elevated flex items-center justify-center">
        <svg className="w-10 h-10 text-muted opacity-40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <rect x="2" y="2" width="20" height="20" rx="2" />
          <path d="M7 2v20M17 2v20M2 7h20M2 12h20M2 17h20" />
        </svg>
      </div>

      <div className="p-3 space-y-2">
        <h3 className="font-display text-base leading-snug text-ink line-clamp-2 group-hover:text-amber transition-colors duration-200">
          {movie.serial_name}
        </h3>

        <div className="flex items-center gap-2 text-xs text-muted">
          {year && <span>{year}</span>}
          {movie.director && (
            <>
              <span className="opacity-40">·</span>
              <span className="truncate">{movie.director}</span>
            </>
          )}
        </div>

        <div className="flex flex-wrap gap-1">
          {movie.genres?.slice(0, 3).map(genre => (
            <span
              key={genre}
              className="px-1.5 py-0.5 text-[0.65rem] font-medium tracking-wide
                         bg-amber-muted text-amber rounded"
            >
              {genre}
            </span>
          ))}
        </div>

        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-1">
            <span className="text-[0.65rem] font-medium text-amber tracking-wide">
              {(movie.score * 100).toFixed(0)}% match
            </span>
          </div>
          {movie.content_type && (
            <span className="text-[0.65rem] text-muted">{movie.content_type}</span>
          )}
        </div>
      </div>
    </a>
  )
}
