// Which drawing plays which agent.
import type { JSX } from 'react'
import { MrKrabs, Patrick, Sandy, SpongeBob, Squidward } from './Characters'

type ArtProps = { size?: number; className?: string; title?: string }

export const CHARACTER_ART: Record<string, (p: ArtProps) => JSX.Element> = {
  boss: MrKrabs,
  inventory: SpongeBob,
  accounting: Squidward,
  customer_service: Patrick,
  facilities: Sandy,
}
