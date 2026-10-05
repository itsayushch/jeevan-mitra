import React from 'react';

// Mushroom Cultivation Hero Art
export const MushroomHeroArt: React.FC<{ className?: string }> = ({ className = "w-full h-40" }) => (
  <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-b from-[#e8efe6] to-[#d6e3d2] flex items-center justify-center p-4 border border-[#c1d4be] shadow-inner ${className}`}>
    <svg viewBox="0 0 400 180" className="w-full h-full max-h-48 drop-shadow-md">
      {/* Background soft soil hills */}
      <path d="M0,150 Q100,120 200,145 T400,140 L400,180 L0,180 Z" fill="#9e8a78" opacity="0.4" />
      <path d="M0,160 Q120,140 240,155 T400,150 L400,180 L0,180 Z" fill="#7d6a58" />

      {/* Straw Grow Bags */}
      {/* Bag 1 Left */}
      <g transform="translate(45, 60)">
        <rect x="0" y="30" width="60" height="70" rx="12" fill="#cbb79d" stroke="#8c7860" strokeWidth="2.5" />
        <ellipse cx="30" cy="30" rx="30" ry="8" fill="#dfcfb8" stroke="#8c7860" strokeWidth="2" />
        {/* Straw lines */}
        <line x1="15" y1="45" x2="35" y2="52" stroke="#aa947b" strokeWidth="2" strokeLinecap="round" />
        <line x1="20" y1="70" x2="45" y2="65" stroke="#aa947b" strokeWidth="2" strokeLinecap="round" />
        {/* Spawn Holes */}
        <circle cx="20" cy="55" r="3" fill="#69533f" />
        <circle cx="42" cy="78" r="3.5" fill="#69533f" />
        <circle cx="25" cy="85" r="3" fill="#69533f" />
        {/* Mushroom Sprouting Left Bag */}
        <path d="M18,52 Q22,38 32,44" stroke="#fdfbf4" strokeWidth="5" fill="none" strokeLinecap="round" />
        <ellipse cx="33" cy="42" rx="14" ry="9" fill="#fdfcf8" stroke="#75614d" strokeWidth="1.8" />
        <ellipse cx="33" cy="44" rx="9" ry="4" fill="#eedccb" />
      </g>

      {/* Bag 2 Middle (Large Hero Bag) */}
      <g transform="translate(145, 30)">
        <rect x="0" y="40" width="85" height="95" rx="16" fill="#decab1" stroke="#8c7860" strokeWidth="3" />
        <ellipse cx="42.5" cy="40" rx="42.5" ry="12" fill="#efe0cc" stroke="#8c7860" strokeWidth="2.5" />
        <path d="M30,30 Q42,10 50,28" stroke="#bda68c" strokeWidth="4" fill="none" />
        {/* Large Mushroom Cluster */}
        {/* Mushroom A */}
        <path d="M42,40 Q40,-5 42,-10" stroke="#fbf8f0" strokeWidth="14" fill="none" strokeLinecap="round" />
        <path d="M12,-8 C12,-35 72,-35 72,-8 C72,5 12,5 12,-8 Z" fill="#9e6647" stroke="#5a3824" strokeWidth="3" />
        {/* Mushroom Gills/Underside */}
        <ellipse cx="42" cy="-4" rx="27" ry="9" fill="#f5ede0" stroke="#5a3824" strokeWidth="1.5" />
        <circle cx="28" cy="-18" r="3" fill="#f5ede0" opacity="0.7" />
        <circle cx="55" cy="-16" r="3.5" fill="#f5ede0" opacity="0.7" />
        <circle cx="42" cy="-22" r="2.5" fill="#f5ede0" opacity="0.7" />

        {/* Baby Mushroom B on Right */}
        <path d="M65,35 Q78,15 85,20" stroke="#fdfcf8" strokeWidth="8" fill="none" strokeLinecap="round" />
        <ellipse cx="86" cy="18" rx="18" ry="11" fill="#b07a58" stroke="#5a3824" strokeWidth="2" />
        <ellipse cx="86" cy="20" rx="12" ry="5" fill="#f5ede0" />

        {/* Baby Pinhead C on Left */}
        <path d="M15,45 Q6,30 10,25" stroke="#fdfcf8" strokeWidth="6" fill="none" strokeLinecap="round" />
        <ellipse cx="10" cy="24" rx="11" ry="8" fill="#a46d4c" stroke="#5a3824" strokeWidth="1.5" />
      </g>

      {/* Bag 3 Right */}
      <g transform="translate(265, 55)">
        <rect x="0" y="35" width="65" height="75" rx="14" fill="#cbb79d" stroke="#8c7860" strokeWidth="2.5" />
        <ellipse cx="32.5" cy="35" rx="32.5" ry="9" fill="#dfcfb8" stroke="#8c7860" strokeWidth="2" />
        <circle cx="20" cy="60" r="3" fill="#69533f" />
        <circle cx="45" cy="72" r="3" fill="#69533f" />
        {/* Sprouting white oyster caps */}
        <path d="M30,35 Q25,8 35,4" stroke="#fefbf3" strokeWidth="9" fill="none" strokeLinecap="round" />
        <ellipse cx="36" cy="4" rx="20" ry="12" fill="#9e6647" stroke="#5a3824" strokeWidth="2" />
        <ellipse cx="36" cy="7" rx="14" ry="6" fill="#f4ece1" />
      </g>
    </svg>
    <div className="absolute bottom-2 left-4 bg-emerald-900/80 backdrop-blur-sm text-emerald-100 text-xs px-2.5 py-1 rounded-full font-semibold flex items-center gap-1.5 shadow">
      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
      NSQF Level 4 Practical Training
    </div>
  </div>
);

// Elder Guide Avatar (Elder Mentor / Sahayak)
export const ElderGuideAvatar: React.FC<{ size?: 'sm' | 'md' | 'lg'; isSpeaking?: boolean }> = ({ size = 'md', isSpeaking = false }) => {
  const dim = size === 'sm' ? 'w-10 h-10' : size === 'lg' ? 'w-20 h-20' : 'w-14 h-14';

  return (
    <div className={`relative flex items-center justify-center rounded-full bg-[#f4ecd8] border-2 border-[#d4be95] p-1 shadow-sm shrink-0 ${dim}`}>
      {isSpeaking && (
        <span className="absolute -inset-1 rounded-full border-2 border-emerald-500 animate-ping opacity-75"></span>
      )}
      <svg viewBox="0 0 100 100" className="w-full h-full">
        {/* Turban / Pagdi in saffron/maroon */}
        <path d="M22,38 C20,18 40,8 52,8 C68,8 82,18 78,38 Z" fill="#d97706" />
        <path d="M26,34 C35,22 62,20 74,32" stroke="#b45309" strokeWidth="4" fill="none" />
        <path d="M30,26 C42,16 60,16 70,24" stroke="#fef3c7" strokeWidth="2" fill="none" opacity="0.6" />
        {/* Face */}
        <ellipse cx="50" cy="52" rx="24" ry="24" fill="#dfa472" />
        {/* Ears */}
        <ellipse cx="25" cy="52" rx="4" ry="7" fill="#c98a58" />
        <ellipse cx="75" cy="52" rx="4" ry="7" fill="#c98a58" />
        {/* Kind Eyes */}
        <ellipse cx="41" cy="48" rx="3.5" ry="3" fill="#2d1e15" />
        <ellipse cx="59" cy="48" rx="3.5" ry="3" fill="#2d1e15" />
        <path d="M36,44 Q41,41 46,43" stroke="#5a3824" strokeWidth="2" fill="none" />
        <path d="M54,43 Q59,41 64,44" stroke="#5a3824" strokeWidth="2" fill="none" />
        {/* Eye crinkles */}
        <line x1="34" y1="48" x2="37" y2="49" stroke="#925c35" strokeWidth="1.2" />
        <line x1="66" y1="48" x2="63" y2="49" stroke="#925c35" strokeWidth="1.2" />
        {/* Nose */}
        <path d="M50,48 L50,56 Q47,58 45,58" stroke="#a36338" strokeWidth="2" fill="none" strokeLinecap="round" />
        {/* White Moustache & Beard */}
        <path d="M34,60 Q50,66 66,60 Q50,78 34,60 Z" fill="#f8fafc" stroke="#cbd5e1" strokeWidth="1" />
        {/* Gentle Smile */}
        <path d="M44,62 Q50,67 56,62" stroke="#b45309" strokeWidth="2" fill="none" strokeLinecap="round" />
        {/* Kurta collar & Shawl */}
        <path d="M26,84 Q50,76 74,84 L80,100 L20,100 Z" fill="#047857" />
        <path d="M38,80 L50,96 L62,80" fill="#f8fafc" />
        {/* Tilak mark */}
        <circle cx="50" cy="38" r="2.5" fill="#dc2626" />
      </svg>
      {isSpeaking && (
        <span className="absolute -bottom-1 -right-1 bg-emerald-600 text-white p-0.5 rounded-full ring-2 ring-white">
          <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
        </span>
      )}
    </div>
  );
};

// Citizen Beneficiary Avatar
export const BeneficiaryAvatar: React.FC<{ size?: 'sm' | 'md' }> = ({ size = 'md' }) => {
  const dim = size === 'sm' ? 'w-8 h-8' : 'w-11 h-11';
  return (
    <div className={`rounded-full bg-amber-100 border border-amber-300 flex items-center justify-center p-0.5 shadow-sm shrink-0 ${dim}`}>
      <svg viewBox="0 0 100 100" className="w-full h-full">
        {/* Hair */}
        <path d="M25,45 C25,20 75,20 75,45 Z" fill="#1e293b" />
        {/* Face */}
        <ellipse cx="50" cy="50" rx="22" ry="22" fill="#d97706" opacity="0.8" />
        {/* Eyes */}
        <circle cx="42" cy="48" r="3" fill="#0f172a" />
        <circle cx="58" cy="48" r="3" fill="#0f172a" />
        {/* Smile */}
        <path d="M43,60 Q50,66 57,60" stroke="#78350f" strokeWidth="2.5" fill="none" strokeLinecap="round" />
        {/* Shirt */}
        <path d="M28,82 Q50,75 72,82 L80,100 L20,100 Z" fill="#0284c7" />
      </svg>
    </div>
  );
};

// Fingerprint Scanner Graphic
export const FingerprintIcon: React.FC<{ className?: string }> = ({ className = "w-16 h-16" }) => (
  <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" className={className}>
    <path d="M50 20 A30 30 0 0 1 80 50" />
    <path d="M50 30 A20 20 0 0 1 70 50" />
    <path d="M50 40 A10 10 0 0 1 60 50" />
    <path d="M50 15 A35 35 0 0 0 15 50 C15 70 28 85 50 88 C70 85 85 70 85 55" />
    <path d="M50 25 A25 25 0 0 0 25 50 C25 65 35 77 50 80 C62 77 72 65 72 52" />
    <path d="M50 35 A15 15 0 0 0 35 50 C35 60 42 70 50 72 C58 70 65 60 65 52" />
    <path d="M45 50 A5 5 0 0 1 55 50" strokeWidth="5" />
  </svg>
);

// Brain Graphic with Synaptic Nodes & Gears
export const BrainNeuralGraphic: React.FC<{ className?: string }> = ({ className = "w-28 h-28" }) => (
  <div className={`relative flex items-center justify-center ${className}`}>
    <svg viewBox="0 0 140 140" className="w-full h-full drop-shadow-md">
      {/* Glow gradient */}
      <defs>
        <radialGradient id="neuralGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#38bdf8" stopOpacity="0" />
        </radialGradient>
      </defs>
      <circle cx="70" cy="70" r="60" fill="url(#neuralGlow)" />

      {/* Left Hemisphere (Biological / Creative / Agri) */}
      <path
        d="M68,30 C50,28 35,40 32,55 C30,65 34,75 32,85 C30,98 42,108 55,108 C62,108 68,104 68,98 Z"
        fill="#e0f2fe"
        stroke="#0284c7"
        strokeWidth="3.5"
      />
      <path d="M40,50 Q52,55 45,70 T60,85" fill="none" stroke="#0284c7" strokeWidth="2.5" strokeDasharray="4 2" />
      <circle cx="45" cy="62" r="3.5" fill="#0284c7" />
      <circle cx="58" cy="80" r="3" fill="#0369a1" />

      {/* Central Divider */}
      <line x1="70" y1="26" x2="70" y2="114" stroke="#0369a1" strokeWidth="3" strokeDasharray="3 3" />

      {/* Right Hemisphere (Logic, Skills, Technical & Gears) */}
      <path
        d="M72,30 C90,28 105,40 108,55 C110,65 106,75 108,85 C110,98 98,108 85,108 C78,108 72,104 72,98 Z"
        fill="#e0f2fe"
        stroke="#0284c7"
        strokeWidth="3.5"
      />

      {/* Gear 1 (Upper Right) */}
      <g transform="translate(88, 52) scale(0.65)">
        <circle cx="0" cy="0" r="14" fill="#38bdf8" stroke="#0369a1" strokeWidth="2" />
        <circle cx="0" cy="0" r="5" fill="#f0f9ff" stroke="#0369a1" strokeWidth="1.5" />
        {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => (
          <rect
            key={deg}
            x="-2.5"
            y="-18"
            width="5"
            height="5"
            rx="1"
            fill="#0284c7"
            transform={`rotate(${deg})`}
          />
        ))}
      </g>

      {/* Gear 2 (Lower Right) */}
      <g transform="translate(85, 82) scale(0.55)">
        <circle cx="0" cy="0" r="14" fill="#0ea5e9" stroke="#0369a1" strokeWidth="2" />
        <circle cx="0" cy="0" r="5" fill="#ffffff" stroke="#0369a1" strokeWidth="1.5" />
        {[0, 60, 120, 180, 240, 300].map((deg) => (
          <rect
            key={deg}
            x="-2.5"
            y="-18"
            width="5"
            height="5"
            rx="1"
            fill="#0369a1"
            transform={`rotate(${deg})`}
          />
        ))}
      </g>

      {/* Circuit Nodes & Connecting Tracks */}
      <polyline points="72,40 82,45 88,40" fill="none" stroke="#0284c7" strokeWidth="2" />
      <circle cx="88" cy="40" r="2.5" fill="#0284c7" />

      <polyline points="72,95 80,98 84,106" fill="none" stroke="#0284c7" strokeWidth="2" />
      <circle cx="84" cy="106" r="2.5" fill="#0284c7" />
    </svg>
  </div>
);

// Animated Waveform Visualizer
export const WaveformVisualizer: React.FC<{ active?: boolean; barCount?: number; color?: string }> = ({
  active = true,
  barCount = 18,
  color = "bg-emerald-600"
}) => {
  const heights = [35, 65, 90, 45, 80, 100, 75, 40, 85, 95, 60, 40, 70, 90, 50, 80, 45, 30];

  return (
    <div className="flex items-center justify-center gap-1 h-12 px-4 py-1">
      {Array.from({ length: barCount }).map((_, i) => {
        const baseH = heights[i % heights.length];
        const heightPercent = active ? baseH : 18;
        const delay = (i * 0.08).toFixed(2);

        return (
          <div
            key={i}
            className={`w-1 rounded-full transition-all duration-300 ${color}`}
            style={{
              height: `${heightPercent}%`,
              animationName: active ? 'pulse' : 'none',
              animationDuration: '1.2s',
              animationTimingFunction: 'ease-in-out',
              animationIterationCount: 'infinite',
              animationDelay: `${delay}s`
            }}
          />
        );
      })}
    </div>
  );
};
