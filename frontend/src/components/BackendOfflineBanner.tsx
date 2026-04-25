interface BackendOfflineBannerProps {
  visible: boolean
  onDismiss: () => void
}

export function BackendOfflineBanner({
  visible,
  onDismiss,
}: BackendOfflineBannerProps) {
  if (!visible) return null

  return (
    <div className="h-10 bg-[#F2E3C7] text-[#6E5A36] border-b border-[#E3D3B3] px-4 flex items-center justify-between">
      <span className="text-sm">
        Backend not running. Start it with: <code>python server.py</code>
      </span>
      <button type="button" onClick={onDismiss} className="text-lg leading-none">
        ×
      </button>
    </div>
  )
}
