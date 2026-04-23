import { NavLink, Outlet } from 'react-router-dom'
import { Terminal, Users, Box, Calculator, Globe } from 'lucide-react'

const navItems = [
  { to: '/', icon: Terminal, label: 'Command Shell' },
  { to: '/agents', icon: Users, label: 'Agent Board' },
  { to: '/models', icon: Box, label: 'Models' },
  { to: '/tokens', icon: Calculator, label: 'Token Calc' },
  { to: '/tumelo', icon: Globe, label: 'Tumelo.com' },
]

export default function App() {
  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <nav className="w-56 bg-obsidian-50 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-cyan glow-cyan font-bold text-lg tracking-wider">NALEDI</h1>
          <p className="text-[10px] text-gray-500 uppercase tracking-widest mt-1">Studex Meat Intelligence</p>
        </div>
        <div className="flex-1 py-2">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 text-sm transition-colors ${
                  isActive
                    ? 'text-cyan bg-cyan/10 border-r-2 border-cyan'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </div>
        <div className="p-4 border-t border-gray-800 text-[10px] text-gray-600">
          SAST {new Date().toLocaleTimeString('en-ZA', { timeZone: 'Africa/Johannesburg' })}
        </div>
      </nav>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
