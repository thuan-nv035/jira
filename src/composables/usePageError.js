import { getErrorMessage } from "../services/api";
import { useToast } from "./useToast";

export function usePageError(error) {
  const toast = useToast();

  function setError(err, silent = false) {
    const message = getErrorMessage(err);
    error.value = message;

    if (!silent) {
      toast.error(message);
    }
  }

  return { setError };
}
