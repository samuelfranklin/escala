import unittest

from infra.database import Member, MemberSquad, Squad, create_tables, session_scope


class OrmDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        create_tables()

    def test_persiste_member_e_squad(self) -> None:
        member_name = "Teste ORM Member"
        squad_name = "Teste ORM Squad"

        with session_scope() as session:
            member = Member(name=member_name, status=True)
            squad = Squad(nome=squad_name)
            session.add(member)
            session.add(squad)

        with session_scope() as session:
            member = session.query(Member).filter(Member.name == member_name).first()
            squad = session.query(Squad).filter(Squad.nome == squad_name).first()
            self.assertIsNotNone(member)
            self.assertIsNotNone(squad)

    def test_relacionamento_member_squad(self) -> None:
        with session_scope() as session:
            member = Member(name="Vinculo Membro", status=True)
            squad = Squad(nome="Vinculo Squad")
            session.add(member)
            session.add(squad)
            session.flush()

            session.add(
                MemberSquad(member_id=member.id, squad_id=squad.id, level=2)
            )

        with session_scope() as session:
            rel = (
                session.query(MemberSquad)
                .filter(MemberSquad.level == 2)
                .order_by(MemberSquad.member_id)
                .first()
            )
            self.assertIsNotNone(rel)


if __name__ == "__main__":
    unittest.main()
