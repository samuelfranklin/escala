import { describe, it, expect } from 'vitest';
import { maskPhone } from './index';

describe('maskPhone', () => {
  it('string vazia retorna vazia', () => {
    expect(maskPhone('')).toBe('');
  });

  it('apenas letras/símbolos retorna vazia', () => {
    expect(maskPhone('abc!@#')).toBe('');
  });

  it('11 dígitos → (11) 99999-9999', () => {
    expect(maskPhone('11999999999')).toBe('(11) 99999-9999');
  });

  it('formatado já → mesmo resultado', () => {
    expect(maskPhone('(11) 99999-9999')).toBe('(11) 99999-9999');
  });

  it('3 dígitos → parcial sem fechar DDD', () => {
    expect(maskPhone('119')).toBe('(11) 9');
  });

  it('2 dígitos → só DDD aberto', () => {
    expect(maskPhone('11')).toBe('(11');
  });

  it('trunca em 11 dígitos', () => {
    expect(maskPhone('119999999991234')).toBe('(11) 99999-9999');
  });
});
