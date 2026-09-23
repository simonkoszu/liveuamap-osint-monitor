/**
 * Google Apps Script - Odbiornik Archiwum Aegis OSINT na Dysk Google
 * 
 * INSTRUKCJA WDROŻENIA (1-2 MINUTY):
 * 1. Otwórz https://script.google.com/ i utwórz nowy projekt (np. "Aegis OSINT Drive Archiver").
 * 2. Wklej poniższy kod do edytora Code.gs.
 * 3. Zastąp FOLDER_ID identyfikatorem swojego folderu na Dysku Google (z adresu URL folderu).
 * 4. Kliknij: Wdróż (Deploy) -> Nowe wdrożenie (New deployment).
 * 5. Wybierz typ: "Aplikacja internetowa" (Web app).
 * 6. Ustaw:
 *    - Wykonaj jako: Ja (twoje konto Google)
 *    - Kto ma dostęp: Każdy (Anyone)
 * 7. Skopiuj wygenerowany URL aplikacji internetowej (https://script.google.com/macros/s/.../exec).
 * 8. W repozytorium GitHub w Settings -> Secrets and variables -> Actions dodaj Secret:
 *    Nazwa: GDRIVE_WEBHOOK_URL
 *    Wartość: [Skopiowany URL Webhooka]
 * 
 * Gotowe! Każde uruchomienie bota będzie automatycznie przesyłać paczkę zarchiwizowanych
 * zdarzeń i tworzyć plik JSON / JSONL w wybranym folderze na Twoim Dysku Google.
 */

const FOLDER_ID = "TUTAJ_WKLEJ_ID_FOLDERU_GOOGLE_DRIVE"; // np. "1AbCdEfGhIjKlMnOpQrStUvWxYz"

function doPost(e) {
  try {
    const rawData = e.postData.contents;
    const payload = JSON.parse(rawData);
    
    let folder;
    if (FOLDER_ID && FOLDER_ID !== "TUTAJ_WKLEJ_ID_FOLDERU_GOOGLE_DRIVE") {
      folder = DriveApp.getFolderById(FOLDER_ID);
    } else {
      // Jeśli brak ID, utwórz folder "Aegis_OSINT_Archiwum" w katalogu głównym
      const folders = DriveApp.getFoldersByName("Aegis_OSINT_Archiwum");
      folder = folders.hasNext() ? folders.next() : DriveApp.createFolder("Aegis_OSINT_Archiwum");
    }
    
    const timestampStr = Utilities.formatDate(new Date(), "GMT", "yyyy-MM-dd_HHmmss");
    const fileName = `aegis_archive_${timestampStr}_batch_${payload.batch_count || 0}.json`;
    
    const file = folder.createFile(fileName, rawData, "application/json");
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      fileId: file.getId(),
      fileName: fileName,
      itemsSaved: payload.batch_count || 0
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
