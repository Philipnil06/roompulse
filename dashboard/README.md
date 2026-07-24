# RoomPulse dashboard

The live RoomPulse dashboard is a vinext/React client that reads the local
FastAPI service. It intentionally owns no persistence or device credentials.

```powershell
npm install
npm run dev
npm run lint
npm test
```

Set `NEXT_PUBLIC_API_URL` when the API is not available at
`http://127.0.0.1:8000`.
