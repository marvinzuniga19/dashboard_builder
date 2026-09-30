export const PAGE_SIZE = 20;

export type ListState = "loading" | "success" | "empty" | "outOfRange" | "error";

export type ListPage = {
  /** Número de página visible, contado desde 1. */
  page: number;
  pageCount: number;
  hasPrevious: boolean;
  hasNext: boolean;
  state: ListState;
};

export type ListPageInput = {
  total: number;
  offset: number;
  pageSize: number;
  /** No se puede decidir el estado hasta tener respuesta o error. */
  isPending: boolean;
  hasError: boolean;
};

/**
 * Traduce la respuesta del listado al estado que ve la persona.
 *
 * El caso delicado es recibir `items: []` con `total > 0`: la página pedida está
 * más allá del final, algo que ocurre al borrar el último elemento de la última
 * página. No es una colección vacía, así que no debe mostrar el estado "vacío" —
que además escondería la paginación—, sino un aviso que permita volver a una
 * página real. Por eso "outOfRange" es un estado propio y no una variante de
 * "empty".
 */
export function resolveListPage(input: ListPageInput): ListPage {
  const { total, offset, pageSize, isPending, hasError } = input;

  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const page = Math.floor(offset / pageSize) + 1;

  let state: ListState;
  if (hasError) {
    state = "error";
  } else if (isPending) {
    state = "loading";
  } else if (total === 0) {
    state = "empty";
  } else if (page > pageCount) {
    state = "outOfRange";
  } else {
    state = "success";
  }

  return {
    page,
    pageCount,
    hasPrevious: offset > 0,
    // `total` sigue siendo válido aunque la página pedida esté vacía: es lo que
    // permite saber que quedan páginas por delante o por detrás.
    hasNext: offset + pageSize < total,
    state,
  };
}
