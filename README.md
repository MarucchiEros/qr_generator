
# QR Code Generator con Password

## Introduzione
Questo applicativo permette di generare QR Code protetti da password. Gli utenti possono creare un QR Code che punta a un URL specifico e opzionalmente proteggerlo con una password. Il QR Code generato può essere utilizzato per un accesso sicuro tramite un form di inserimento password.

## Funzionalità principali
- **Generazione di QR Code**: Gli utenti possono inserire un URL e una password per generare un QR Code.
- **Protezione con password**: Ogni QR Code può essere protetto da una password.
- **Verifica della password**: Gli utenti che scansionano il QR Code verranno reindirizzati a un form per l'inserimento della password.

## Come far partire l'applicazione

### Prerequisiti
1. **Python 3.x**: Assicurati di avere Python installato. Puoi verificare la versione con il comando:
   ```bash
   python --version
   ```

2. **MySQL**: L'applicazione utilizza un database MySQL. Assicurati che MySQL sia installato e in esecuzione. La configurazione predefinita è `root` come nome utente e nessuna password per il database `qr_code_db`.

### Passaggi per avviare l'applicazione

#### 1. Esegui un tunnel SSH per esporre il server Flask
Per poter accedere all'applicazione attraverso un URL pubblico, è necessario avviare un tunnel SSH tramite Pinggy. Usa il comando seguente per stabilire la connessione:

```bash
ssh -p 443 -R0:127.0.0.1:8000 a.pinggy.io
```

Questo comando creerà un tunnel che permetterà di accedere all'applicazione Flask tramite Pinggy.

#### 2. Avvia l'applicazione
Apri un altro terminale e naviga fino alla cartella del progetto. Per avviare l'applicazione, esegui il seguente comando:

```bash
python app.py
```

Questo comando avvierà il server Flask sulla porta `8000` del tuo computer locale. Ora l'applicazione sarà disponibile tramite l'URL generato da Pinggy.

#### 3. Accedere all'applicazione
Una volta che il tunnel SSH è attivo e il server Flask è in esecuzione, potrai accedere all'applicazione tramite il link generato da Pinggy. L'URL sarà del tipo:

```
https://rnuen-164-128-168-41.a.free.pinggy.link
```

### Come funziona
- **Generazione del QR Code**: Nella home page dell'app, inserisci l'URL che desideri codificare in un QR Code. Puoi anche impostare una password opzionale per proteggere il QR Code.
- **Validazione tramite password**: Quando un utente scansiona il QR Code, verrà indirizzato a una pagina di validazione dove dovrà inserire la password (se presente) per essere reindirizzato all'URL protetto.

### Configurazione del database
L'applicazione utilizza un database MySQL chiamato `qr_code_db`. La configurazione del database prevede l'utente `root` senza password. Assicurati che il database esista e che la connessione sia corretta.

1. **Apri MySQL Workbench** con il nome utente `root` e senza password.
2. **Crea il database** eseguendo il seguente comando:
   ```sql
   CREATE DATABASE qr_code_db;
   ```

### Dipendenze
L'applicazione richiede le seguenti librerie Python:
blinker==1.9.0
click==8.1.8
colorama==0.4.6
Flask==3.1.0
Flask-SQLAlchemy==3.1.1
greenlet==3.1.1
itsdangerous==2.2.0
Jinja2==3.1.5
MarkupSafe==3.0.2
mysqlclient==2.2.7
pillow==11.1.0
qrcode==8.0
SQLAlchemy==2.0.37
typing_extensions==4.12.2
Werkzeug==3.1.3

Puoi installare tutte le dipendenze eseguendo:

```bash
pip install -r requirements.txt
```

