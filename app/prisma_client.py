from prisma import Prisma

class PrismaClient:
    _instance = None

    @staticmethod
    async def get_instance():
        
        if PrismaClient._instance is None:
            PrismaClient._instance = Prisma()
            await PrismaClient._instance.connect()

        return PrismaClient._instance

    @staticmethod
    async def close_connection():
        if PrismaClient._instance is not None:
            await PrismaClient._instance.disconnect()
            PrismaClient._instance = None
