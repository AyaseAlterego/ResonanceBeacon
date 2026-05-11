interface TitleBarProps {
  onMinimize?: () => void;
  onMaximize?: () => void;
  onClose?: () => void;
  pythonConnected: boolean;
}

export default function TitleBar({ onMinimize, onMaximize, onClose, pythonConnected }: TitleBarProps) {
  return (
    <div
      className="flex items-center h-[38px] px-4 select-none"
      style={{ backgroundColor: '#0d0d14', WebkitAppRegion: 'drag' as unknown as string }}
    >
      <div className="flex items-center gap-2" style={{ WebkitAppRegion: 'no-drag' as unknown as string }}>
        <div
          className="w-3 h-3 rounded-full bg-red-500 hover:brightness-125 cursor-pointer"
          onClick={onClose}
        />
        <div
          className="w-3 h-3 rounded-full bg-yellow-500 hover:brightness-125 cursor-pointer"
          onClick={onMinimize}
        />
        <div
          className="w-3 h-3 rounded-full bg-green-500 hover:brightness-125 cursor-pointer"
          onClick={onMaximize}
        />
      </div>

      <div className="flex-1 text-center">
        <span className="text-sm text-gray-400 font-medium tracking-wide">
          起源信标 · ResonanceBeacon
        </span>
      </div>

      <div className="flex items-center gap-2" style={{ WebkitAppRegion: 'no-drag' as unknown as string }}>
        <div
          className={`w-2 h-2 rounded-full ${pythonConnected ? 'bg-green-500' : 'bg-red-500'}`}
        />
        <span className="text-xs text-gray-500">
          {pythonConnected ? '后端在线' : '后端离线'}
        </span>
      </div>
    </div>
  );
}
