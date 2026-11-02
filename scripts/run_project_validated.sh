#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly ROOT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd -P)"
readonly PIPELINE_VERSION="1.4.3"
readonly CACHE_SCHEMA="v1.4.2"

CURRENT_STAGE="inicialização"

on_error() {
    local status="$1"
    local line="$2"
    local command="$3"
    printf 'ERRO: etapa="%s" linha=%s código=%s comando=%q\n' \
        "${CURRENT_STAGE}" "${line}" "${status}" "${command}" >&2
    exit "${status}"
}

trap 'on_error "$?" "$LINENO" "$BASH_COMMAND"' ERR

abort_run() {
    local status="$1"
    local line="$2"
    local command="$3"
    local message="$4"
    printf 'ERRO: etapa="%s" linha=%s código=%s comando=%q mensagem=%s\n' \
        "${CURRENT_STAGE}" "${line}" "${status}" "${command}" "${message}" >&2
    exit "${status}"
}

usage() {
    cat <<'EOF'
Uso:
  ./scripts/run_project_validated.sh <project_id>
  ./scripts/run_project_validated.sh --check <project_id>
  ./scripts/run_project_validated.sh --resume <project_id>
  ./scripts/run_project_validated.sh --recover <project_id>
  ./scripts/run_project_validated.sh --help

Por padrão, executa a pipeline limpa com --no-resume. Os modos --resume e
--recover preservam e reutilizam outputs e checkpoints existentes.

Opções:
  --check   Verifica somente pré-requisitos; não inicia a análise.
  --resume  Retoma uma execução com manifesto compatível.
  --recover Valida quatro CSVs iniciais, cria um manifesto ausente e retoma.
  -h, --help
            Exibe esta ajuda e encerra.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
fi

RUN_MODE="clean"
case "${1:-}" in
    --check)
        RUN_MODE="check"
        shift
        ;;
    --resume)
        RUN_MODE="resume"
        shift
        ;;
    --recover)
        RUN_MODE="recover"
        shift
        ;;
esac

if [[ "$#" -ne 1 ]]; then
    usage >&2
    abort_run 64 "${LINENO}" "validar argumentos" "informe exatamente um project_id"
fi

readonly PROJECT_ID="$1"
if [[ ! "${PROJECT_ID}" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]]; then
    abort_run 64 "${LINENO}" "validar project_id" "project_id inválido: ${PROJECT_ID}"
fi

readonly CONFIG_REL="configs/${PROJECT_ID}.yml"
readonly CONFIG_PATH="${ROOT_DIR}/${CONFIG_REL}"
readonly VENV_DIR="${ROOT_DIR}/.venv"
readonly PYTHON="${VENV_DIR}/bin/python"
readonly PYTEST="${VENV_DIR}/bin/pytest"
readonly HOTSPOTS="${VENV_DIR}/bin/hotspots"
readonly LOG_DIR="${ROOT_DIR}/logs"
readonly AUDIT_LOG="${LOG_DIR}/${PROJECT_ID}_v${PIPELINE_VERSION}_audit.log"
readonly RUN_LOG="${LOG_DIR}/${PROJECT_ID}_v${PIPELINE_VERSION}_run.log"
readonly VALIDATION_ROOT="${ROOT_DIR}/results/validation/v${PIPELINE_VERSION}"
readonly PROJECT_VALIDATION_DIR="${VALIDATION_ROOT}/${PROJECT_ID}"
readonly SUMMARY_PATH="${PROJECT_VALIDATION_DIR}/execution_summary.txt"

CURRENT_STAGE="verificação de pré-requisitos"
if [[ ! -f "${CONFIG_PATH}" ]]; then
    abort_run 66 "${LINENO}" "test -f ${CONFIG_PATH}" \
        "configuração não encontrada"
fi
if [[ ! -d "${VENV_DIR}" ]]; then
    abort_run 69 "${LINENO}" "test -d ${VENV_DIR}" \
        "ambiente virtual não encontrado"
fi
for executable in "${PYTHON}" "${PYTEST}" "${HOTSPOTS}"; do
    if [[ ! -x "${executable}" ]]; then
        abort_run 69 "${LINENO}" "test -x ${executable}" \
            "executável ausente ou sem permissão"
    fi
done
if [[ ! -f "${ROOT_DIR}/scripts/validate_pipeline.py" ]]; then
    abort_run 66 "${LINENO}" \
        "test -f ${ROOT_DIR}/scripts/validate_pipeline.py" \
        "validador independente não encontrado"
fi

cd "${ROOT_DIR}"
"${PYTHON}" -c \
    'import hotspots; from hotspots.pipeline import CACHE_SCHEMA; import hotspots.output_validation; assert hotspots.__version__ == "1.4.3" and CACHE_SCHEMA == "v1.4.2"'

if [[ "${RUN_MODE}" == "check" ]]; then
    printf 'Pré-requisitos válidos para %s (pipeline %s, cache %s).\n' \
        "${PROJECT_ID}" "${PIPELINE_VERSION}" "${CACHE_SCHEMA}"
    exit 0
fi

mkdir -p "${LOG_DIR}" "${PROJECT_VALIDATION_DIR}"

CURRENT_STAGE="testes automatizados"
"${PYTEST}" -q

if [[ "${RUN_MODE}" == "recover" ]]; then
    CURRENT_STAGE="recuperação do manifesto"
    "${PYTHON}" -m hotspots.recovery \
        --config "${CONFIG_REL}" \
        --outputs outputs \
        --workers 4
fi

CURRENT_STAGE="auditoria do projeto"
"${HOTSPOTS}" audit --config "${CONFIG_REL}" \
    > >(tee "${AUDIT_LOG}") 2>&1

CURRENT_STAGE="execução da pipeline"
RUN_ARGS=(
    run
    --config "${CONFIG_REL}"
    --output outputs
    --workers 4
)
if [[ "${RUN_MODE}" == "clean" ]]; then
    RUN_ARGS+=(--no-resume)
fi
"${HOTSPOTS}" "${RUN_ARGS[@]}" > >(tee "${RUN_LOG}") 2>&1

CURRENT_STAGE="validação independente"
"${PYTHON}" "${ROOT_DIR}/scripts/validate_pipeline.py" \
    --project "${PROJECT_ID}" \
    --config "${CONFIG_REL}" \
    --outputs outputs \
    --validation "results/validation/v${PIPELINE_VERSION}"

CURRENT_STAGE="verificações de integridade e resumo"
"${PYTHON}" -m hotspots.output_validation \
    --project "${PROJECT_ID}" \
    --outputs "${ROOT_DIR}/outputs" \
    --validation "${VALIDATION_ROOT}" \
    --summary "${SUMMARY_PATH}"

CURRENT_STAGE="geração de checksums SHA-256"
(
    cd "${PROJECT_VALIDATION_DIR}"
    find . -maxdepth 1 -type f ! -name SHA256SUMS -print0 \
        | sort -z \
        | xargs -0 -r sha256sum > SHA256SUMS
)

CURRENT_STAGE="conclusão"
printf 'Execução validada concluída para %s.\n' "${PROJECT_ID}"
printf 'Resumo: %s\n' "${SUMMARY_PATH}"
printf 'Checksums: %s\n' "${PROJECT_VALIDATION_DIR}/SHA256SUMS"
