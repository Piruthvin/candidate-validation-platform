interface StartupErrorProps {
  message: string;
}

export function StartupError({ message }: StartupErrorProps) {
  return (
    <div className="flex h-screen w-screen flex-col items-center justify-center bg-[#0B0B0B] p-6 text-center">
      <div className="flex max-w-md flex-col items-center gap-6 rounded-3xl border border-[#2A2A2A] bg-[#151515] p-10 shadow-2xl">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10">
          <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Startup Error</h2>
          <p className="mt-2 text-sm text-[#CFCFCF]">{message}</p>
        </div>
      </div>
    </div>
  );
}
