// Classes partagées par les composants (spec 0003, *États communs*). Chaînes complètes,
// jamais construites à la volée, pour que Tailwind les trouve dans les sources.

/** Assemble des classes en ignorant les valeurs vides. */
export function cx(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(' ')
}

/** Anneau de focus : 2 px violet, décalé de 2 px, au focus clavier seulement. */
export const focusRing =
  'outline-hidden demo-focus-visible:outline-2 demo-focus-visible:outline-solid demo-focus-visible:outline-offset-2 demo-focus-visible:outline-accent'

/** Anneau de focus d'un champ de saisie : à tout focus, clavier, clic ou toucher. */
export const fieldFocusRing =
  'outline-hidden data-[focused]:outline-2 data-[focused]:outline-solid data-[focused]:outline-offset-2 data-[focused]:outline-accent demo-focus-visible:outline-2 demo-focus-visible:outline-solid demo-focus-visible:outline-offset-2 demo-focus-visible:outline-accent'

/** Hauteur : 32 px à la souris, zone de 44 × 44 px au doigt. */
export const touchSize = 'pointer-fine:min-h-8 pointer-coarse:min-h-11 pointer-coarse:min-w-11'

/** Désactivé : opacité 50 %, curseur interdit (exception voulue au contraste). */
export const disabled = 'data-[disabled]:cursor-not-allowed data-[disabled]:opacity-50'

/** Transition courte des couleurs (survol, focus). */
export const quick = 'transition-colors duration-(--duration-fast)'

/**
 * Lien isolé du cockpit (un `<a>` simple : l'anneau suit :focus-visible, que le navigateur réserve au clavier).
 * Même zone que les boutons : 32 px de haut à la souris, 44 × 44 px au doigt.
 */
export const link = cx(
  'inline-flex items-center rounded-sm font-medium text-accent underline-offset-4 hover:underline',
  touchSize,
  'outline-hidden focus-visible:outline-2 focus-visible:outline-solid focus-visible:outline-offset-2 focus-visible:outline-accent',
)

/** Fond de la liste d'un `Select` (aussi utilisé par la vitrine pour montrer la liste ouverte). */
export const listBox = 'max-h-72 overflow-auto rounded-md border border-line bg-panel p-1 outline-hidden shadow-lg shadow-ink'

/** Option d'une liste. */
export const listBoxItem = cx(
  'flex cursor-default items-center gap-2 rounded-sm px-2.5 py-1.5 text-sm text-text outline-hidden',
  'pointer-coarse:min-h-11 data-[focused]:bg-panel-2 data-[hovered]:bg-panel-2 data-[selected]:text-accent',
  disabled,
)
