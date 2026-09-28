"""Garde des routes réservées au trader connecté.

La méthode de connexion n'est pas encore décidée (spec « Connexion », scope n°6).
En attendant, la garde est **fermée** : toute route protégée répond 401, pour
qu'aucune donnée ne sorte sans connexion. La fonction Connexion remplacera
`require_session` par la vraie vérification de session.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status


async def require_session() -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="connexion requise"
    )


SessionDep = Annotated[None, Depends(require_session)]
