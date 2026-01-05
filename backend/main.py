import asyncio
import os
from fastapi import FastAPI, Depends
import ping3
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Opcional se for servir arquivos, mas vamos fazer via HTML direto
from fastapi.responses import HTMLResponse

load_dotenv()
DEVICES = [
    {"name": "Servidor Interno", "ip": os.getenv("IP_SERVIDOR_INTERNO")}, 
    {"name": "Servidor de arquivos", "ip": os.getenv("IP_SERVIDOR_ARQUIVOS")},
]

# --- 2. CONFIGURAÇÃO DO BANCO DE DADOS (SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./sentinela.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo da Tabela de Logs (O Histórico)
class PingLog(Base):
    __tablename__ = "ping_logs"
    id = Column(Integer, primary_key=True, index=True)
    device_name = Column(String)
    ip_address = Column(String)
    is_up = Column(Boolean)
    latency_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)

# Cria o arquivo do banco de dados se não existir
Base.metadata.create_all(bind=engine)

# Dependência para pegar o banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 3. LÓGICA DE MONITORIZAÇÃO (O Robô) ---
async def monitor_network():
    """Esta função roda em loop infinito no background"""
    while True:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] A verificar rede...")
        db = SessionLocal()
        try:
            for dev in DEVICES:
                response = ping3.ping(dev["ip"], unit='ms', timeout=1)
                
                is_up = response is not None
                latency = round(response, 2) if is_up else None
                
                # Regra de Negócio: Só gravar se falhar OU a cada 5 rodadas para não encher o banco?
                # Por enquanto, vamos gravar TUDO para ver o histórico bonito.
                new_log = PingLog(
                    device_name=dev["name"],
                    ip_address=dev["ip"],
                    is_up=is_up,
                    latency_ms=latency
                )
                db.add(new_log)
            db.commit()
        except Exception as e:
            print(f"Erro no monitoramento: {e}")
        finally:
            db.close()
        
        # Espera 30 segundos antes da próxima verificação
        await asyncio.sleep(30)

# --- 4. APLICAÇÃO WEB (FastAPI) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia o monitoramento quando a API liga
    asyncio.create_task(monitor_network())
    yield
    # (Aqui poderia ter código para desligar, se necessário)

app = FastAPI(title="Sentinela 2.0", lifespan=lifespan)
# Configuração de CORS (Permite que o browser acesse a API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção isso seria restrito, mas pra dev ok
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Geral"])
def read_root():
    return {"status": "Monitoramento Ativo", "db": "SQLite Conectado"}

@app.get("/history", tags=["Relatórios"])
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    """Retorna os últimos 50 registos de monitoramento"""
    logs = db.query(PingLog).order_by(PingLog.timestamp.desc()).limit(limit).all()
    return logs

@app.get("/failures", tags=["Relatórios"])
def get_failures(db: Session = Depends(get_db)):
    """Retorna apenas quando houve queda de conexão"""
    logs = db.query(PingLog).filter(PingLog.is_up == False).order_by(PingLog.timestamp.desc()).all()
    return logs