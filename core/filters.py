"""Parameterized global filters shared by all business dashboards."""
from dataclasses import dataclass
import streamlit as st


@dataclass(frozen=True)
class BusinessFilters:
    statuses: tuple[str, ...]
    states: tuple[str, ...]

    def where(self, alias: str = 'f') -> tuple[str, list[str]]:
        # alias is a hardcoded identifier supplied by our own metric modules.
        if alias not in {'f', 'o', 'r', 'p'}:
            raise ValueError('Unsupported fact-table alias')
        if not self.statuses or not self.states:
            return 'WHERE 1 = 0', []
        status_marks = ', '.join('?' for _ in self.statuses)
        state_marks = ', '.join('?' for _ in self.states)
        return (f'WHERE {alias}.order_status IN ({status_marks}) '
                f'AND {alias}.customer_state IN ({state_marks})',
                [*self.statuses, *self.states])


def render_global_filters(con) -> BusinessFilters:
    statuses = [r[0] for r in con.execute(
        'SELECT DISTINCT order_status FROM fact_orders WHERE order_status IS NOT NULL ORDER BY 1'
    ).fetchall()]
    states = [r[0] for r in con.execute(
        'SELECT DISTINCT customer_state FROM fact_orders WHERE customer_state IS NOT NULL ORDER BY 1'
    ).fetchall()]
    with st.sidebar:
        st.header('🎯 Global Filters')
        chosen_status = st.multiselect('Order Status:', statuses,
                                      default=['delivered'] if 'delivered' in statuses else statuses)
        chosen_states = st.multiselect('Customer State (Region):', states,
                                      default=states, help='All states selected by default.')
    # Retain previous app behavior: an empty multiselect means all.
    return BusinessFilters(tuple(chosen_status or statuses), tuple(chosen_states or states))
