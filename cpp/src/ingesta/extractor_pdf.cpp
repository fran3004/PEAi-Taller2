#include "pea/ingesta/extractor_pdf.hpp"
#include <QCoreApplication>
#include <QCryptographicHash>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonArray>
#include <QProcess>
#include <QStandardPaths>
#include <stdexcept>

namespace pea::ingesta {
QJsonObject procesar_pdf(const QString& ruta) {
    QFile entrada(ruta);
    if (!entrada.open(QIODevice::ReadOnly) || entrada.size() > 64 * 1024 * 1024)
        throw std::runtime_error("No se pudo leer el PDF o excede 64 MiB.");
    const auto bytes = entrada.readAll();
    if (!bytes.startsWith("%PDF-")) throw std::invalid_argument("El archivo no tiene una cabecera PDF válida.");
    QString herramienta = QCoreApplication::applicationDirPath() + "/pdftotext.exe";
    if (!QFileInfo::exists(herramienta)) herramienta = QStandardPaths::findExecutable("pdftotext");
    if (herramienta.isEmpty()) throw std::runtime_error("Falta pdftotext. Extraiga el paquete completo o instale Poppler UCRT64.");
    QProcess proceso;
    proceso.start(herramienta, {"-layout", "-enc", "UTF-8", QFileInfo(ruta).absoluteFilePath(), "-"});
    if (!proceso.waitForStarted(5000)) throw std::runtime_error("No se pudo iniciar el lector PDF.");
    if (!proceso.waitForFinished(60000)) {
        proceso.kill(); proceso.waitForFinished(5000);
        throw std::runtime_error("El procesamiento PDF superó el tiempo permitido.");
    }
    if (proceso.exitStatus() != QProcess::NormalExit || proceso.exitCode() != 0)
        throw std::runtime_error("El lector rechazó el PDF; puede estar dañado o protegido.");
    QString texto = QString::fromUtf8(proceso.readAllStandardOutput());
    QStringList paginas = texto.split(QChar('\f'));
    if (!paginas.isEmpty() && paginas.last().trimmed().isEmpty()) paginas.removeLast();
    QJsonArray extraidas, advertencias;
    int caracteres = 0, sospechosas = 0;
    for (qsizetype i = 0; i < paginas.size(); ++i) {
        const auto contenido = paginas[i].trimmed();
        const bool escaneada = contenido.size() < 20;
        if (escaneada) { sospechosas++; advertencias.append(QString("Página %1 sin texto suficiente: puede requerir OCR.").arg(i + 1)); }
        caracteres += contenido.size();
        extraidas.append(QJsonObject{{"numero", static_cast<int>(i + 1)}, {"texto", contenido}, {"es_escaneada_sospechosa", escaneada}});
    }
    return {{"ruta_archivo", QFileInfo(ruta).absoluteFilePath()},
            {"sha256", QString::fromLatin1(QCryptographicHash::hash(bytes, QCryptographicHash::Sha256).toHex())},
            {"total_paginas", static_cast<int>(paginas.size())}, {"total_caracteres", caracteres},
            {"es_escaneado", !paginas.isEmpty() && sospechosas * 2 >= paginas.size()},
            {"advertencias", advertencias}, {"paginas", extraidas}};
}
}
